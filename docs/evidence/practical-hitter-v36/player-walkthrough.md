# MLB event logit model player review

Next-year eight-event MLB count likelihood, 144 source-count/context inputs, explicit mature-training league offsets and completed-origin prediction offsets. Legacy batting-value quality and workload predictors excluded. Same evaluation players and V34 expected PA. Physically coherent probabilities are not automatically a useful batting forecast.

Ten fixed diagnostics plus largest delivered-value gain/harm, false high/low and ordinary example. Peers use only origin stage/debut/age/MLB and upper-minor workload/quality/draft rank/college status. Outcome-selected cases are diagnosis, not independent confirmation.

## Jeff McNeil: 2018 to 2019

Selection: Predeclared diagnostic.

Age 26; draft pick 356, class unknown; captured listing 1 is soft. Full actual model features and saved fit are in cases.json; no individual target count/environment enters forecast inputs.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | AA | 14 | 1 | 1 | 2 |
| 2017 | AAA | 78 | 1 | 10 | 3 |
| 2017 | Aplus | 116 | 3 | 19 | 6 |
| 2018 | AA | 241 | 14 | 23 | 21 |
| 2018 | AAA | 143 | 5 | 19 | 13 |
| 2018 | MLB | 248 | 3 | 24 | 13 |

Each logit is log(origin league probability) + fitted linear effect; softmax gives eight probabilities summing to one. Other is the anchored category.

| Event | Origin league probability | Linear odds effect | Forecast probability | Actual next count | Batting wins/600 contribution |
|---|---:|---:|---:|---:|---:|
| other | 0.465785 | 0.00000 | 0.542647 | 276 | 0.00000 |
| K | 0.222573 | -0.61791 | 0.139781 | 75 | -0.00000 |
| UBB | 0.079708 | -0.45046 | 0.059184 | 33 | -0.71492 |
| HBP | 0.010381 | -0.09852 | 0.010960 | 21 | 0.02101 |
| 1B | 0.142174 | 0.07864 | 0.179187 | 100 | 1.63365 |
| 2B | 0.044637 | -0.12029 | 0.046109 | 38 | 0.09143 |
| 3B | 0.004575 | 0.25900 | 0.006906 | 1 | 0.18253 |
| HR | 0.030167 | -0.83633 | 0.015228 | 23 | -1.49435 |

The contribution column uses existing neutral event values divided by wOBA scale and ten runs/win; sum equals the predicted batting rate. K/other affect other probabilities but have zero direct wOBA weight.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 399.170 | -0.22474 | 1.07943 |
| event | 399.170 | -0.28066 | 1.04223 |
| Actual | 567 | 3.35684 | 4.90426 |

Final product: fixed PA × (rate/600 + origin replacement 0.0030788). Saved numerical fit: {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 165, 'objective': 1.4563131432292091, 'maximum_gradient': 7.46914516148496e-07}; 1019 distinct active training people.

Largest actual linear-effect terms (columns K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| pooled_MLB_K | -0.94943 | -0.51258, -0.18335, -0.18013, 0.01097, -0.07271, 0.00385, -0.33833 |
| intercept | 1.00000 | 0.33121, 0.04354, 0.05253, -0.03818, -0.01891, 0.11593, -0.05188 |
| pooled_MLB_BB | -0.19655 | -0.02308, -0.15652, -0.01412, 0.02038, -0.00737, 0.00738, -0.02645 |
| position_4 | 1.00000 | -0.04304, -0.02334, 0.01152, 0.01704, -0.03308, 0.03844, -0.15298 |
| pooled_AA_K | -0.96629 | -0.13583, -0.06720, -0.06474, -0.02046, -0.03298, 0.00401, -0.13034 |
| pooled_AAA_K | -0.66280 | -0.09604, -0.02420, -0.04528, -0.01712, -0.04388, -0.01182, -0.10596 |
| pooled_MLB_BABIP | 0.38926 | 0.00924, 0.01314, 0.00862, 0.09516, 0.02910, 0.04062, -0.04474 |
| draft_class_unknown | 1.00000 | -0.04390, -0.03545, 0.06325, 0.00962, -0.04149, -0.02481, -0.07177 |
| pooled_MLB_HR | -0.12759 | -0.01174, -0.00909, -0.00635, 0.01532, -0.01052, 0.01334, -0.06384 |
| pooled_MLB_pa | 0.41333 | -0.01141, 0.02282, -0.00774, 0.00434, 0.01954, -0.01564, 0.06033 |
| on_40man | 1.00000 | -0.05329, -0.02004, 0.04043, -0.00087, 0.00463, -0.01284, 0.02825 |
| draft_known | 1.00000 | 0.00301, 0.02840, 0.02893, -0.01208, 0.01586, 0.04497, 0.00961 |

The model recognizes contact: predicted K 14% and singles 17.9%, versus league 22.3% and 14.2%. But it predicts only 1.52% HR despite 19 current upper-minor HR and 3 MLB HR; weak walk/power projections offset the contact gain. Rate falls −0.225→−0.281, worsening value with fixed 399 PA versus actual 567/4.90. This is not missing contact data. Mullins and O'Brien fail while Lowe succeeds; McNeil's exceptional development is not a certainty.

Origin-selected peers: Cedric Mullins (age 23, MLB/AAA/AA PA 191/269.0/218.0, draft 403/unknown; actual 74 PA/-0.798 wins); Brandon Lowe (age 23, MLB/AAA/AA PA 148/205.0/240.0, draft 87/unknown; actual 327 PA/2.038 wins); Peter O'Brien (age 27, MLB/AAA/AA PA 74/135.0/286.0, draft 94/unknown; actual 47 PA/-0.191 wins).

Profile support: all=354 distinct people; active=279 distinct people.

## Spencer Steer: 2022 to 2023

Selection: Predeclared diagnostic.

Age 24; draft pick 90, class unknown; captured listing 1 is soft. Full actual model features and saved fit are in cases.json; no individual target count/environment enters forecast inputs.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | AA | 280 | 14 | 73 | 19 |
| 2021 | Aplus | 208 | 10 | 32 | 35 |
| 2022 | AA | 156 | 8 | 23 | 14 |
| 2022 | AAA | 336 | 15 | 66 | 36 |
| 2022 | MLB | 108 | 2 | 26 | 11 |

Each logit is log(origin league probability) + fitted linear effect; softmax gives eight probabilities summing to one. Other is the anchored category.

| Event | Origin league probability | Linear odds effect | Forecast probability | Actual next count | Batting wins/600 contribution |
|---|---:|---:|---:|---:|---:|
| other | 0.467680 | 0.00000 | 0.448227 | 289 | -0.00000 |
| K | 0.224178 | 0.14342 | 0.247988 | 139 | 0.00000 |
| UBB | 0.078977 | 0.19334 | 0.091838 | 68 | 0.44796 |
| HBP | 0.011239 | 0.14939 | 0.012507 | 11 | 0.04606 |
| 1B | 0.142135 | -0.11684 | 0.121201 | 95 | -0.92397 |
| 2B | 0.043614 | 0.04666 | 0.043796 | 37 | 0.01134 |
| 3B | 0.003532 | 0.07405 | 0.003645 | 3 | 0.00887 |
| HR | 0.028646 | 0.11495 | 0.030799 | 23 | 0.21536 |

The contribution column uses existing neutral event values divided by wOBA scale and ten runs/win; sum equals the predicted batting rate. K/other affect other probabilities but have zero direct wOBA weight.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 180.375 | -0.23663 | 0.49361 |
| event | 180.375 | -0.19438 | 0.50631 |
| Actual | 665 | 1.90921 | 4.17493 |

Final product: fixed PA × (rate/600 + origin replacement 0.0031310). Saved numerical fit: {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 174, 'objective': 1.4640188200817275, 'maximum_gradient': 9.162475346539709e-07}; 1387 distinct active training people.

Largest actual linear-effect terms (columns K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.30409, 0.01037, 0.05004, -0.01801, 0.00835, 0.11638, -0.05787 |
| position_5 | 1.00000 | 0.01195, 0.01181, 0.01190, -0.00554, 0.02118, -0.07920, 0.09197 |
| age_centered | -0.60000 | -0.00519, 0.01552, -0.05096, 0.01215, 0.02840, 0.07428, 0.08909 |
| pooled_MLB_BB | 0.11346 | 0.01372, 0.08837, 0.00548, -0.00926, 0.00322, -0.00416, 0.01385 |
| pooled_Aplus_BB | 0.55135 | 0.00351, 0.07095, -0.00615, -0.00463, 0.01106, 0.00242, -0.00262 |
| draft_known | 1.00000 | -0.01435, 0.01539, 0.06845, -0.01324, 0.00442, 0.03362, -0.00943 |
| draft_class_unknown | 1.00000 | -0.03711, -0.02279, 0.06019, 0.00261, -0.03131, -0.03043, -0.06405 |
| pooled_Aplus_K | -0.47568 | -0.05599, -0.01602, -0.01522, 0.00645, -0.00127, 0.00846, -0.03708 |
| pooled_AAA_BB | 0.20917 | 0.01013, 0.05538, 0.00137, -0.00454, 0.00134, -0.00268, 0.00674 |
| pooled_AAA_K | -0.25872 | -0.04226, -0.01173, -0.01924, -0.00469, -0.01945, -0.00043, -0.04585 |
| prior_debut | 1.00000 | -0.03947, -0.00864, 0.00579, -0.01536, -0.00449, -0.01159, -0.00654 |
| on_40man | 1.00000 | -0.03862, -0.00723, 0.02743, 0.00204, 0.00487, -0.00681, -0.00545 |

108 MLB PA and 492 upper-minor PA/23 HR are visible. The event profile gives favorable walks/power but weak singles and 24.8% K. Rate improves only −0.237→−0.194 and value 0.494→0.506 versus 665/4.17 actual. Fixed PA remains the principal opportunity deficit; the event model does not solve it. Brennan, Freeman and Henderson have different later workloads.

Origin-selected peers: Will Brennan (age 24, MLB/AAA/AA PA 45/433.0/157.0, draft 250/unknown; actual 455 PA/0.166 wins); Tyler Freeman (age 23, MLB/AAA/AA PA 86/343.0/0.0, draft 71/unknown; actual 168 PA/0.094 wins); Gunnar Henderson (age 21, MLB/AAA/AA PA 132/295.0/208.0, draft 42/unknown; actual 622 PA/3.402 wins).

Profile support: all=336 distinct people; active=298 distinct people.

## Masyn Winn: 2023 to 2024

Selection: Predeclared diagnostic.

Age 21; draft pick 54, class HS SR; captured listing 1 is soft. Full actual model features and saved fit are in cases.json; no individual target count/environment enters forecast inputs.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | A | 284 | 3 | 60 | 40 |
| 2021 | Aplus | 154 | 2 | 40 | 6 |
| 2022 | AA | 403 | 11 | 86 | 50 |
| 2022 | Aplus | 147 | 1 | 29 | 13 |
| 2023 | AAA | 498 | 18 | 83 | 44 |
| 2023 | MLB | 137 | 2 | 26 | 10 |

Each logit is log(origin league probability) + fitted linear effect; softmax gives eight probabilities summing to one. Other is the anchored category.

| Event | Origin league probability | Linear odds effect | Forecast probability | Actual next count | Batting wins/600 contribution |
|---|---:|---:|---:|---:|---:|
| other | 0.456074 | 0.00000 | 0.472905 | 330 | 0.00000 |
| K | 0.227279 | -0.04028 | 0.226362 | 109 | -0.00000 |
| UBB | 0.083350 | -0.05435 | 0.081854 | 40 | -0.05210 |
| HBP | 0.011472 | -0.26906 | 0.009089 | 1 | -0.08655 |
| 1B | 0.141393 | -0.10025 | 0.132626 | 105 | -0.38695 |
| 2B | 0.044692 | -0.08137 | 0.042720 | 32 | -0.12250 |
| 3B | 0.003867 | 0.31687 | 0.005505 | 5 | 0.12826 |
| HR | 0.031873 | -0.13284 | 0.028938 | 15 | -0.29359 |

The contribution column uses existing neutral event values divided by wOBA scale and ten runs/win; sum equals the predicted batting rate. K/other affect other probabilities but have zero direct wOBA weight.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 305.512 | -0.79671 | 0.54021 |
| event | 305.512 | -0.81343 | 0.53170 |
| Actual | 637 | 0.25454 | 2.25951 |

Final product: fixed PA × (rate/600 + origin replacement 0.0030961). Saved numerical fit: {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 157, 'objective': 1.4665133151968568, 'maximum_gradient': 8.707906871236109e-07}; 1470 distinct active training people.

Largest actual linear-effect terms (columns K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.29444, -0.00026, 0.07039, -0.01295, 0.00529, 0.08998, -0.09409 |
| age_centered | -1.20000 | -0.01641, 0.02533, -0.09081, 0.02404, 0.05486, 0.15585, 0.17630 |
| position_6 | 1.00000 | -0.03531, -0.08361, -0.10583, -0.00372, -0.03174, 0.05355, -0.17382 |
| pooled_MLB_K | -0.23249 | -0.12841, -0.04830, -0.03004, 0.00338, -0.01667, -0.00260, -0.08350 |
| pooled_MLB_BABIP | -0.51269 | -0.01166, -0.01394, -0.02634, -0.11963, -0.04491, -0.05071, 0.05820 |
| pooled_AAA_K | -0.52742 | -0.08458, -0.02259, -0.03818, -0.00853, -0.03760, -0.00190, -0.09153 |
| pooled_AA_BB | 0.33636 | -0.00396, 0.06967, 0.00312, -0.01264, 0.00046, -0.00153, 0.00571 |
| draft_known | 1.00000 | -0.01435, 0.01858, 0.06003, -0.01381, 0.00282, 0.03435, -0.01775 |
| prior_debut | 1.00000 | -0.04986, -0.01501, 0.00190, -0.01905, -0.00547, -0.00700, 0.00402 |
| pooled_MLB_HR | -0.08903 | -0.00444, -0.00689, -0.00414, 0.01160, -0.00660, 0.00788, -0.04337 |
| pooled_MLB_pa | 0.22833 | -0.00616, 0.01547, -0.00521, -0.00092, 0.01049, -0.00384, 0.03628 |
| draft_hs | 1.00000 | 0.02104, 0.00121, -0.03403, -0.01460, 0.00209, 0.01924, 0.03537 |

Strong AAA 498 PA/18 HR/83 K coexist with weak 137 MLB PA. Predicted K 22.6% is plausible but singles/walk/power contributions leave rate −0.813 versus old −0.797 and actual +0.254. With fixed 306 PA versus 637 actual, delivered value remains too low. The model does not erase source coverage but still fails to translate the combined evidence usefully. Meadows, Edwards and Soderstrom provide contrasting outcomes.

Origin-selected peers: Parker Meadows (age 23, MLB/AAA/AA PA 145/517.0/0.0, draft 44/HS SR; actual 298 PA/1.211 wins); Xavier Edwards (age 23, MLB/AAA/AA PA 84/433.0/0.0, draft 38/HS SR; actual 303 PA/2.187 wins); Tyler Soderstrom (age 21, MLB/AAA/AA PA 138/335.0/0.0, draft 26/HS SR; actual 213 PA/0.873 wins).

Profile support: all=384 distinct people; active=342 distinct people.

## Nick Kurtz: 2024 to 2025

Selection: Predeclared diagnostic.

Age 21; draft pick 4, class 4YR JR; captured listing 0 is soft. Full actual model features and saved fit are in cases.json; no individual target count/environment enters forecast inputs.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

Each logit is log(origin league probability) + fitted linear effect; softmax gives eight probabilities summing to one. Other is the anchored category.

| Event | Origin league probability | Linear odds effect | Forecast probability | Actual next count | Batting wins/600 contribution |
|---|---:|---:|---:|---:|---:|
| other | 0.465823 | 0.00000 | 0.432224 | 154 | -0.00000 |
| K | 0.225800 | 0.22325 | 0.261919 | 151 | 0.00000 |
| UBB | 0.079036 | 0.11898 | 0.082601 | 60 | 0.12418 |
| HBP | 0.011072 | -0.01282 | 0.010142 | 2 | -0.03376 |
| 1B | 0.141968 | -0.00125 | 0.131564 | 58 | -0.45921 |
| 2B | 0.042593 | 0.07362 | 0.042540 | 26 | -0.00327 |
| 3B | 0.003820 | 0.16631 | 0.004186 | 2 | 0.02865 |
| HR | 0.029888 | 0.22771 | 0.034824 | 36 | 0.49375 |

The contribution column uses existing neutral event values divided by wOBA scale and ten runs/win; sum equals the predicted batting rate. K/other affect other probabilities but have zero direct wOBA weight.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 42.495 | -0.13556 | 0.12316 |
| event | 42.495 | 0.15034 | 0.14341 |
| Actual | 489 | 5.15001 | 5.72099 |

Final product: fixed PA × (rate/600 + origin replacement 0.0031242). Saved numerical fit: {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 176, 'objective': 1.4672341460847973, 'maximum_gradient': 9.639855797945422e-07}; 1545 distinct active training people.

Largest actual linear-effect terms (columns K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.27975, 0.00530, 0.03940, -0.00376, -0.01876, 0.10519, -0.14699 |
| age_centered | -1.20000 | -0.01425, 0.00069, -0.07512, 0.01844, 0.04814, 0.17739, 0.18027 |
| position_3 | 1.00000 | 0.03096, 0.03814, 0.01152, 0.01039, 0.03088, -0.11047, 0.13393 |
| draft_known | 1.00000 | 0.01430, 0.03645, 0.06694, -0.02561, -0.00213, 0.03087, -0.00079 |
| age_squared | 1.44000 | -0.02682, -0.01491, -0.02767, -0.01853, -0.01136, -0.05128, 0.03868 |
| draft_rank | 0.81761 | -0.02947, 0.00239, -0.01818, 0.00900, 0.01301, -0.00323, 0.03296 |
| pooled_A_BB | 0.53333 | -0.00563, 0.02729, -0.00114, -0.00550, -0.00127, -0.00104, 0.01227 |
| draft_college | 1.00000 | -0.02312, 0.00618, -0.00895, 0.00314, 0.01437, 0.00561, -0.02009 |
| pooled_AA_BB | 0.06957 | -0.00090, 0.01438, -0.00121, -0.00187, 0.00148, -0.00049, 0.00140 |
| pooled_A_BABIP | 0.15789 | 0.00007, 0.00030, -0.00499, 0.00951, -0.00202, 0.00321, 0.00278 |
| elapsed_scaled | -0.10000 | -0.00036, 0.00108, 0.00683, -0.00135, 0.00158, 0.00764, -0.00427 |
| pooled_A_HR | 0.21852 | 0.00704, 0.00253, -0.00060, -0.00583, -0.00038, -0.00142, 0.00552 |

Only 50 pro PA and a known fourth-overall college pick are available. Predicted HR 3.48% and K 26.2% produce modest positive rate 0.150, improving old −0.136, but fixed 42 PA leaves value near 0.14 versus 489/5.72 actual. This is not a solved exceptional-arrival forecast. Adding college status to origin-only peer matching selects Moore, Smith and Davis: two advance, one does not, improving the relevance of comparisons without promising Kurtz's outcome.

Origin-selected peers: Christian Moore (age 21, MLB/AAA/AA PA 0/0.0/98.0, draft 8/4YR JR; actual 184 PA/0.198 wins); Cam Smith (age 21, MLB/AAA/AA PA 0/0.0/20.0, draft 14/4YR SO; actual 493 PA/1.014 wins); Chase Davis (age 22, MLB/AAA/AA PA 0/0.0/31.0, draft 21/4YR JR; actual 0 PA/0.000 wins).

Profile support: all=11 distinct people; active=0 distinct people.

## Aaron Judge: 2016 to 2017

Selection: Predeclared diagnostic; false low.

Age 24; draft pick 32, class unknown; captured listing 1 is soft. Full actual model features and saved fit are in cases.json; no individual target count/environment enters forecast inputs.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2014 | A | 278 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 8 | 72 | 49 |
| 2015 | AA | 280 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 4 | 42 | 9 |

Each logit is log(origin league probability) + fitted linear effect; softmax gives eight probabilities summing to one. Other is the anchored category.

| Event | Origin league probability | Linear odds effect | Forecast probability | Actual next count | Batting wins/600 contribution |
|---|---:|---:|---:|---:|---:|
| other | 0.474130 | 0.00000 | 0.327511 | 195 | -0.00000 |
| K | 0.211193 | 0.95934 | 0.380755 | 208 | 0.00000 |
| UBB | 0.076693 | 0.57779 | 0.094409 | 116 | 0.61712 |
| HBP | 0.008945 | 0.34148 | 0.008693 | 5 | -0.00912 |
| 1B | 0.149198 | 0.03039 | 0.106240 | 75 | -1.89605 |
| 2B | 0.044718 | 0.20567 | 0.037943 | 24 | -0.42088 |
| 3B | 0.004730 | 0.25271 | 0.004206 | 3 | -0.04098 |
| HR | 0.030393 | 0.65064 | 0.040242 | 52 | 0.98518 |

The contribution column uses existing neutral event values divided by wOBA scale and ten runs/win; sum equals the predicted batting rate. K/other affect other probabilities but have zero direct wOBA weight.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 143.966 | -0.05720 | 0.43085 |
| event | 143.966 | -0.76474 | 0.26109 |
| Actual | 678 | 5.32988 | 8.10841 |

Final product: fixed PA × (rate/600 + origin replacement 0.0030881). Saved numerical fit: {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 165, 'objective': 1.4464694951370143, 'maximum_gradient': 7.004012520210166e-07}; 856 distinct active training people.

Largest actual linear-effect terms (columns K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| pooled_MLB_K | 1.03333 | 0.59117, 0.21369, 0.20296, -0.02206, 0.09433, -0.01453, 0.39983 |
| intercept | 1.00000 | 0.33029, 0.07943, 0.09704, -0.05414, 0.00817, 0.10148, -0.02525 |
| pooled_Aplus_BB | 0.58007 | 0.01827, 0.10457, -0.01010, 0.00293, 0.01965, -0.00108, -0.00415 |
| position_9 | 1.00000 | 0.00354, 0.00314, -0.00350, 0.03274, 0.01395, 0.08039, 0.06574 |
| age_centered | -0.60000 | 0.00609, 0.00516, -0.03402, 0.02449, 0.03047, 0.06632, 0.07987 |
| draft_class_unknown | 1.00000 | -0.03612, -0.04274, 0.05065, 0.00707, -0.05210, -0.02665, -0.07428 |
| pooled_AAA_BB | 0.28914 | 0.01210, 0.07398, -0.00101, 0.00322, -0.00712, -0.00069, 0.00052 |
| pooled_MLB_BB | 0.07179 | 0.00709, 0.05706, 0.00481, -0.00741, 0.00367, -0.00274, 0.00963 |
| draft_known | 1.00000 | 0.00678, 0.01838, 0.00934, -0.00683, 0.01177, 0.04664, 0.02621 |
| on_40man | 1.00000 | -0.04464, -0.01383, 0.02773, -0.01031, -0.00044, -0.00734, 0.01470 |
| prior_debut | 1.00000 | -0.01831, 0.01361, 0.03468, -0.03961, 0.00699, -0.00736, -0.00275 |
| pooled_A_BABIP | 0.54518 | 0.02502, -0.00204, -0.01546, 0.03703, 0.00262, 0.01096, 0.00561 |

95 debut PA/42 K and 410 current AAA PA/19 HR/98 K are present. The logit coefficient on MLB K dominates and cross-loads positively onto HR, yielding 38.1% projected K and 4.02% HR. Rate drops −0.057→−0.765, worsening the largest false low against 678/8.11 actual. It illustrates overweighting a brief debut in this specification, not absent minor history. Marrero, Decker and Cowart had poor outcomes; no automatic future MVP claim follows.

Origin-selected peers: Deven Marrero (age 25, MLB/AAA/AA PA 14/388.0/0.0, draft 24/unknown; actual 188 PA/-0.447 wins); Jaff Decker (age 26, MLB/AAA/AA PA 57/417.0/0.0, draft 42/unknown; actual 62 PA/-0.115 wins); Kaleb Cowart (age 24, MLB/AAA/AA PA 87/458.0/0.0, draft 18/unknown; actual 117 PA/0.123 wins).

Profile support: all=186 distinct people; active=159 distinct people.

## Aaron Judge: 2024 to 2025

Selection: Predeclared diagnostic; largest harm.

Age 32; draft pick 32, class unknown; captured listing 1 is soft. Full actual model features and saved fit are in cases.json; no individual target count/environment enters forecast inputs.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 696 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 58 | 171 | 113 |

Each logit is log(origin league probability) + fitted linear effect; softmax gives eight probabilities summing to one. Other is the anchored category.

| Event | Origin league probability | Linear odds effect | Forecast probability | Actual next count | Batting wins/600 contribution |
|---|---:|---:|---:|---:|---:|
| other | 0.465823 | 0.00000 | 0.395760 | 245 | -0.00000 |
| K | 0.225800 | 0.29385 | 0.257366 | 160 | 0.00000 |
| UBB | 0.079036 | 0.70191 | 0.135478 | 88 | 1.96608 |
| HBP | 0.011072 | 0.15933 | 0.011031 | 7 | -0.00147 |
| 1B | 0.141968 | -0.02650 | 0.117461 | 94 | -1.08169 |
| 2B | 0.042593 | 0.10809 | 0.040317 | 30 | -0.14136 |
| 3B | 0.003820 | 0.01754 | 0.003303 | 2 | -0.04050 |
| HR | 0.029888 | 0.43636 | 0.039284 | 53 | 0.93991 |

The contribution column uses existing neutral event values divided by wOBA scale and ten runs/win; sum equals the predicted batting rate. K/other affect other probabilities but have zero direct wOBA weight.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 548.496 | 4.55334 | 5.87607 |
| event | 548.496 | 1.64096 | 3.21369 |
| Actual | 679 | 6.28743 | 9.23105 |

Final product: fixed PA × (rate/600 + origin replacement 0.0031242). Saved numerical fit: {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 169, 'objective': 1.466762138167451, 'maximum_gradient': 9.055527421834082e-07}; 1554 distinct active training people.

Largest actual linear-effect terms (columns K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| pooled_MLB_BB | 0.70756 | 0.07987, 0.54785, 0.03312, -0.06219, 0.01403, -0.03257, 0.10417 |
| pooled_MLB_pa | 2.48000 | -0.07024, 0.18549, -0.05883, -0.00264, 0.13493, -0.07363, 0.38613 |
| intercept | 1.00000 | 0.26369, -0.02838, 0.03385, -0.00699, -0.02759, 0.07579, -0.14645 |
| pooled_MLB_HR | 0.50479 | 0.03676, 0.04913, 0.01959, -0.06657, 0.03777, -0.04390, 0.24678 |
| position_8 | 1.00000 | 0.00503, -0.01356, 0.02840, 0.01962, -0.02972, 0.22512, -0.09398 |
| age_centered | 1.00000 | 0.00425, -0.02058, 0.08703, -0.01884, -0.04968, -0.12091, -0.15695 |
| pooled_MLB_K | 0.23778 | 0.12600, 0.04389, 0.03359, -0.00342, 0.01815, 0.00322, 0.08018 |
| pooled_MLB_BABIP | 0.38435 | 0.01212, 0.00568, 0.00510, 0.09525, 0.03257, 0.03752, -0.04220 |
| draft_class_unknown | 1.00000 | -0.02510, -0.02137, 0.06216, -0.00149, -0.02047, -0.01216, -0.02942 |
| elapsed_scaled | 0.80000 | -0.00799, -0.00911, -0.04792, 0.00845, 0.00026, -0.06015, 0.04145 |
| prior_debut | 1.00000 | -0.05660, -0.02185, 0.00043, -0.02194, 0.00316, -0.00499, -0.01009 |
| draft_known | 1.00000 | 0.01451, 0.03434, 0.05170, -0.02194, 0.00004, 0.04616, -0.01192 |

Largest deterioration. The recent MLB record contains 704 PA/58 HR, 458/37 and 696/62. Nevertheless projected HR is only 3.93%, versus 7.8% realized next year; rate drops 4.55→1.64 and value 5.88→3.21 with PA fixed 548. The model learns walks but heavily compresses elite power. This is a baseball-reasonability failure, not merely an unforeseeable future breakout. Freeman, Betts and Olson are useful productive contrasts. A model that understands these count inputs should retain substantially more established power evidence.

Origin-selected peers: Freddie Freeman (age 34, MLB/AAA/AA PA 638/0.0/0.0, draft 78/unknown; actual 627 PA/4.784 wins); Mookie Betts (age 31, MLB/AAA/AA PA 516/0.0/0.0, draft 172/unknown; actual 663 PA/2.398 wins); Matt Olson (age 30, MLB/AAA/AA PA 685/0.0/0.0, draft 47/unknown; actual 724 PA/5.517 wins).

Profile support: all=224 distinct people; active=170 distinct people.

## Matt Olson: 2022 to 2023

Selection: Predeclared diagnostic.

Age 28; draft pick 47, class unknown; captured listing 1 is soft. Full actual model features and saved fit are in cases.json; no individual target count/environment enters forecast inputs.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 245 | 14 | 77 | 32 |
| 2021 | MLB | 673 | 39 | 113 | 76 |
| 2022 | MLB | 699 | 34 | 170 | 69 |

Each logit is log(origin league probability) + fitted linear effect; softmax gives eight probabilities summing to one. Other is the anchored category.

| Event | Origin league probability | Linear odds effect | Forecast probability | Actual next count | Batting wins/600 contribution |
|---|---:|---:|---:|---:|---:|
| other | 0.467680 | 0.00000 | 0.438465 | 281 | -0.00000 |
| K | 0.224178 | 0.09427 | 0.230950 | 167 | 0.00000 |
| UBB | 0.078977 | 0.36250 | 0.106395 | 96 | 0.95505 |
| HBP | 0.011239 | -0.00650 | 0.010468 | 4 | -0.02798 |
| 1B | 0.142135 | -0.09937 | 0.120651 | 88 | -0.94825 |
| 2B | 0.043614 | 0.10501 | 0.045417 | 27 | 0.11201 |
| 3B | 0.003532 | -0.22818 | 0.002636 | 3 | -0.07019 |
| HR | 0.028646 | 0.51654 | 0.045017 | 54 | 1.63766 |

The contribution column uses existing neutral event values divided by wOBA scale and ten runs/win; sum equals the predicted batting rate. K/other affect other probabilities but have zero direct wOBA weight.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 572.650 | 1.85799 | 3.56624 |
| event | 572.650 | 1.65831 | 3.37567 |
| Actual | 720 | 4.57082 | 7.71416 |

Final product: fixed PA × (rate/600 + origin replacement 0.0031310). Saved numerical fit: {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 174, 'objective': 1.4644482516382542, 'maximum_gradient': 8.150798471823216e-07}; 1390 distinct active training people.

Largest actual linear-effect terms (columns K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| pooled_MLB_pa | 2.30733 | -0.05936, 0.14749, -0.08036, 0.00412, 0.10433, -0.09400, 0.35371 |
| intercept | 1.00000 | 0.24769, 0.00729, 0.02990, 0.01009, -0.01240, 0.14659, -0.09230 |
| pooled_MLB_BB | 0.25767 | 0.02892, 0.19975, 0.00633, -0.02373, 0.00152, -0.00974, 0.03387 |
| position_3 | 1.00000 | 0.03340, 0.05696, -0.05705, 0.00864, 0.02895, -0.10789, 0.12301 |
| pooled_MLB_HR | 0.21603 | 0.01079, 0.01987, 0.00965, -0.02831, 0.01857, -0.01962, 0.10648 |
| draft_known | 1.00000 | 0.00758, 0.03328, 0.08114, -0.02077, 0.01108, 0.02484, 0.01318 |
| pooled_MLB_BABIP | -0.28686 | 0.00124, -0.00246, -0.01258, -0.07332, -0.02455, -0.02576, 0.03534 |
| draft_class_unknown | 1.00000 | -0.03215, -0.02094, 0.04091, 0.00205, -0.02491, -0.02454, -0.05138 |
| pooled_MLB_K | -0.07957 | -0.04441, -0.01449, -0.01356, 0.00180, -0.00403, -0.00139, -0.02727 |
| draft_elapsed | 1.00000 | -0.01282, -0.03825, -0.01138, 0.04076, -0.01115, 0.00449, -0.02713 |
| elapsed_scaled | 0.60000 | -0.00161, -0.01271, -0.02150, -0.00109, -0.00103, -0.03874, 0.02589 |
| prior_debut | 1.00000 | -0.02062, -0.02119, 0.01301, -0.03630, 0.01187, -0.01444, 0.00508 |

699/673/245 actual MLB PA with 34/39/14 HR support a power hitter. The model predicts 4.50% HR, plausible but conservative versus the later 54 HR/720 PA breakout. Rate falls 1.858→1.658 and value 3.57→3.38, slightly worsening the miss. Fixed PA is independently conservative. Alonso, Reynolds and Bell play regularly without Olson's exact breakout; this case is less glaring than established Judge but part of the same power compression.

Origin-selected peers: Pete Alonso (age 27, MLB/AAA/AA PA 685/0.0/0.0, draft 64/unknown; actual 658 PA/3.452 wins); Bryan Reynolds (age 27, MLB/AAA/AA PA 614/0.0/0.0, draft 59/unknown; actual 640 PA/3.040 wins); Josh Bell (age 29, MLB/AAA/AA PA 647/0.0/0.0, draft 61/unknown; actual 617 PA/2.116 wins).

Profile support: all=569 distinct people; active=455 distinct people.

## Gavin Lux: 2023 to 2024

Selection: Predeclared diagnostic.

Age 25; draft pick 20, class unknown; captured listing 1 is soft. Full actual model features and saved fit are in cases.json; no individual target count/environment enters forecast inputs.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 74 | 1 | 15 | 6 |
| 2021 | MLB | 381 | 7 | 83 | 38 |
| 2022 | MLB | 471 | 6 | 95 | 47 |

Each logit is log(origin league probability) + fitted linear effect; softmax gives eight probabilities summing to one. Other is the anchored category.

| Event | Origin league probability | Linear odds effect | Forecast probability | Actual next count | Batting wins/600 contribution |
|---|---:|---:|---:|---:|---:|
| other | 0.456074 | 0.00000 | 0.451506 | 221 | -0.00000 |
| K | 0.227279 | -0.01814 | 0.220958 | 110 | -0.00000 |
| UBB | 0.083350 | 0.12603 | 0.093598 | 44 | 0.35697 |
| HBP | 0.011472 | 0.02807 | 0.011680 | 2 | 0.00757 |
| 1B | 0.141393 | 0.04990 | 0.147139 | 74 | 0.25360 |
| 2B | 0.044692 | -0.00047 | 0.044224 | 24 | -0.02909 |
| 3B | 0.003867 | 0.18348 | 0.004600 | 2 | 0.05735 |
| HR | 0.031873 | -0.18227 | 0.026296 | 10 | -0.55789 |

The contribution column uses existing neutral event values divided by wOBA scale and ten runs/win; sum equals the predicted batting rate. K/other affect other probabilities but have zero direct wOBA weight.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 215.427 | -0.23943 | 0.58101 |
| event | 215.427 | 0.08852 | 0.69876 |
| Actual | 487 | 0.08394 | 1.58897 |

Final product: fixed PA × (rate/600 + origin replacement 0.0030961). Saved numerical fit: {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 155, 'objective': 1.4667463539183347, 'maximum_gradient': 6.243015172346006e-07}; 1468 distinct active training people.

Largest actual linear-effect terms (columns K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.29207, 0.00427, 0.04299, -0.01487, -0.02219, 0.08278, -0.11254 |
| pooled_MLB_pa | 1.00900 | -0.03380, 0.07140, -0.01883, -0.00065, 0.05600, -0.03070, 0.15431 |
| position_4 | 1.00000 | -0.04491, -0.02420, -0.00945, 0.00843, -0.03015, 0.05556, -0.14036 |
| pooled_MLB_BB | 0.16966 | 0.01850, 0.13265, 0.00855, -0.01531, 0.00299, -0.00765, 0.02474 |
| pooled_MLB_K | -0.19056 | -0.10183, -0.03562, -0.02838, 0.00235, -0.01389, -0.00078, -0.06503 |
| age_centered | -0.40000 | 0.00065, 0.00985, -0.03239, 0.00843, 0.02004, 0.04839, 0.06424 |
| pooled_MLB_HR | -0.12988 | -0.00816, -0.01263, -0.00555, 0.01782, -0.00958, 0.01163, -0.06382 |
| draft_class_unknown | 1.00000 | -0.03935, -0.03349, 0.05557, 0.00432, -0.02564, -0.00588, -0.04181 |
| pooled_MLB_BABIP | 0.20568 | 0.00480, 0.00025, 0.00322, 0.05305, 0.01809, 0.01999, -0.02315 |
| draft_known | 1.00000 | 0.00916, 0.03192, 0.05163, -0.01784, 0.00430, 0.04144, -0.00844 |
| prior_debut | 1.00000 | -0.04579, -0.01551, 0.00217, -0.02666, 0.00555, -0.00678, -0.00128 |
| on_40man | 1.00000 | -0.04454, -0.00983, 0.02594, -0.00072, -0.00712, -0.00142, 0.01502 |

Prior 471 and 381 MLB PA survive the current missed season. Predicted event rate +0.089 nearly matches actual +0.084, improving old −0.239; fixed 215 PA still falls far below actual 487. This is a genuinely useful rate example but not an opportunity repair. Plummer, Ciuffo and Craig all fail to return and remain weak medical-return analogues; no generic inactive penalty is validated.

Origin-selected peers: Nick Plummer (age 26, MLB/AAA/AA PA 0/0.0/0.0, draft 23/unknown; actual 0 PA/0.000 wins); Nick Ciuffo (age 28, MLB/AAA/AA PA 0/0.0/0.0, draft 21/unknown; actual 0 PA/0.000 wins); Will Craig (age 28, MLB/AAA/AA PA 0/0.0/0.0, draft 22/unknown; actual 0 PA/0.000 wins).

Profile support: all=111 distinct people; active=9 distinct people.

## Matt McLain: 2024 to 2025

Selection: Predeclared diagnostic.

Age 24; draft pick 17, class 4YR JR; captured listing 0 is soft. Full actual model features and saved fit are in cases.json; no individual target count/environment enters forecast inputs.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | AA | 452 | 17 | 127 | 69 |
| 2023 | AAA | 180 | 12 | 37 | 29 |
| 2023 | MLB | 403 | 16 | 115 | 31 |

Each logit is log(origin league probability) + fitted linear effect; softmax gives eight probabilities summing to one. Other is the anchored category.

| Event | Origin league probability | Linear odds effect | Forecast probability | Actual next count | Batting wins/600 contribution |
|---|---:|---:|---:|---:|---:|
| other | 0.465823 | 0.00000 | 0.404406 | 238 | -0.00000 |
| K | 0.225800 | 0.38461 | 0.287974 | 167 | 0.00000 |
| UBB | 0.079036 | 0.28814 | 0.091529 | 55 | 0.43517 |
| HBP | 0.011072 | 0.01260 | 0.009734 | 5 | -0.04859 |
| 1B | 0.141968 | 0.05378 | 0.130060 | 79 | -0.52559 |
| 2B | 0.042593 | 0.15625 | 0.043230 | 18 | 0.03961 |
| 3B | 0.003820 | 0.31568 | 0.004548 | 0 | 0.05697 |
| HR | 0.029888 | 0.09449 | 0.028519 | 15 | -0.13696 |

The contribution column uses existing neutral event values divided by wOBA scale and ten runs/win; sum equals the predicted batting rate. K/other affect other probabilities but have zero direct wOBA weight.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 173.516 | 0.21812 | 0.60517 |
| event | 173.516 | -0.17939 | 0.49021 |
| Actual | 577 | -1.27881 | 0.56815 |

Final product: fixed PA × (rate/600 + origin replacement 0.0031242). Saved numerical fit: {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 176, 'objective': 1.4672341460847973, 'maximum_gradient': 9.639855797945422e-07}; 1545 distinct active training people.

Largest actual linear-effect terms (columns K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.27975, 0.00530, 0.03940, -0.00376, -0.01876, 0.10519, -0.14699 |
| pooled_MLB_K | 0.42254 | 0.22683, 0.08072, 0.05024, -0.01138, 0.02799, 0.00837, 0.14635 |
| position_6 | 1.00000 | -0.04665, -0.08975, -0.11545, -0.00485, -0.03579, 0.05935, -0.15436 |
| pooled_MLB_BABIP | 0.55153 | 0.00546, 0.00727, 0.02579, 0.13664, 0.04388, 0.04917, -0.07506 |
| pooled_AAA_BB | 0.47869 | 0.00458, 0.11855, 0.00190, -0.01011, -0.00266, -0.00392, -0.00198 |
| pooled_AA_BB | 0.53082 | -0.00689, 0.10972, -0.00922, -0.01429, 0.01127, -0.00373, 0.01068 |
| pooled_MLB_pa | 0.53733 | -0.01285, 0.03821, -0.00606, -0.00278, 0.03085, -0.02168, 0.09073 |
| age_centered | -0.60000 | -0.00712, 0.00034, -0.03756, 0.00922, 0.02407, 0.08870, 0.09014 |
| prior_debut | 1.00000 | -0.07972, -0.03063, -0.00634, -0.02205, 0.01195, -0.00408, -0.00228 |
| draft_known | 1.00000 | 0.01430, 0.03645, 0.06694, -0.02561, -0.00213, 0.03087, -0.00079 |
| pooled_AA_K | 0.37241 | 0.05576, 0.02166, 0.01585, 0.00640, 0.01007, 0.00465, 0.03485 |
| pooled_AAA_HR | 0.21639 | -0.01307, -0.00375, 0.00849, -0.01183, 0.01459, -0.00715, 0.04476 |

Known 403 MLB PA/16 HR and 180 AAA PA/12 HR remain, followed by no current play. Predicted K 28.8% and HR 2.85% reduce rate 0.218→−0.179 toward actual −1.279. Delivered value becomes 0.49 versus 0.57 actual, partly because fixed PA is only 174 versus 577. Keep the rate gain distinct from lucky product cancellation and the unresolved return role. Swaggerty, Walker and Proctor all have zero next-year PA and are not equivalent injury-return cases.

Origin-selected peers: Travis Swaggerty (age 26, MLB/AAA/AA PA 0/0.0/0.0, draft 10/JR; actual 0 PA/0.000 wins); Steele Walker (age 27, MLB/AAA/AA PA 0/0.0/0.0, draft 46/JR; actual 0 PA/0.000 wins); Ford Proctor (age 27, MLB/AAA/AA PA 0/0.0/0.0, draft 92/JR; actual 0 PA/0.000 wins).

Profile support: all=5 distinct people; active=4 distinct people.

## Fernando Tatis Jr.: 2022 to 2023

Selection: Predeclared diagnostic.

Age 23; draft pick None, class unknown; captured listing 0 is soft. Full actual model features and saved fit are in cases.json; no individual target count/environment enters forecast inputs.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 257 | 17 | 61 | 26 |
| 2021 | MLB | 546 | 42 | 153 | 56 |
| 2022 | AA | 14 | 0 | 2 | 4 |

Each logit is log(origin league probability) + fitted linear effect; softmax gives eight probabilities summing to one. Other is the anchored category.

| Event | Origin league probability | Linear odds effect | Forecast probability | Actual next count | Batting wins/600 contribution |
|---|---:|---:|---:|---:|---:|
| other | 0.467680 | 0.00000 | 0.419758 | 290 | -0.00000 |
| K | 0.224178 | 0.33990 | 0.282658 | 141 | 0.00000 |
| UBB | 0.078977 | 0.22145 | 0.088456 | 53 | 0.33016 |
| HBP | 0.011239 | -0.07999 | 0.009312 | 3 | -0.06999 |
| 1B | 0.142135 | -0.06904 | 0.119061 | 89 | -1.01846 |
| 2B | 0.043614 | 0.07603 | 0.042237 | 33 | -0.08552 |
| 3B | 0.003532 | 0.13487 | 0.003628 | 1 | 0.00750 |
| HR | 0.028646 | 0.30534 | 0.034891 | 25 | 0.62478 |

The contribution column uses existing neutral event values divided by wOBA scale and ten runs/win; sum equals the predicted batting rate. K/other affect other probabilities but have zero direct wOBA weight.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 147.175 | 1.27950 | 0.77465 |
| event | 147.175 | -0.21153 | 0.40891 |
| Actual | 635 | 0.72681 | 2.73521 |

Final product: fixed PA × (rate/600 + origin replacement 0.0031310). Saved numerical fit: {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 160, 'objective': 1.4609854981415449, 'maximum_gradient': 7.846913628555669e-07}; 1394 distinct active training people.

Largest actual linear-effect terms (columns K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.27820, 0.00330, 0.05214, -0.02155, -0.02309, 0.15393, -0.07270 |
| pooled_MLB_HR | 0.37728 | 0.01516, 0.01916, 0.01947, -0.04964, 0.03661, -0.03399, 0.18636 |
| pooled_MLB_K | 0.33386 | 0.18112, 0.06749, 0.04743, -0.00486, 0.02133, 0.00639, 0.11030 |
| position_6 | 1.00000 | -0.04552, -0.08785, -0.14471, -0.00444, -0.03981, 0.03471, -0.16147 |
| pooled_MLB_pa | 0.98500 | -0.03279, 0.05447, -0.01543, 0.00042, 0.05376, -0.04519, 0.15423 |
| pooled_MLB_BB | 0.18987 | 0.02587, 0.14208, 0.00693, -0.01799, 0.00553, -0.00608, 0.02355 |
| age_centered | -0.80000 | 0.01048, 0.00313, -0.05429, 0.01193, 0.04019, 0.09898, 0.12256 |
| draft_class_unknown | 1.00000 | -0.02907, -0.01602, 0.06384, 0.01335, -0.02182, -0.01653, -0.03847 |
| pooled_AA_BB | 0.25263 | 0.00083, 0.05773, -0.00148, -0.00766, -0.00187, -0.00287, 0.00335 |
| pooled_MLB_BABIP | 0.14505 | -0.00093, 0.00071, 0.00586, 0.03640, 0.01076, 0.01525, -0.01834 |
| prior_debut | 1.00000 | -0.03298, -0.00996, 0.00488, -0.02096, -0.00132, -0.01483, -0.01985 |
| age_squared | 0.64000 | -0.01074, -0.00425, -0.02959, -0.00773, -0.00693, -0.02376, 0.01332 |

Past MLB 546 PA/42 HR and 257/17 remain, while only a 14-PA AA stint is current. Predicted HR 3.49% and K 28.3% lower rate 1.279→−0.211 and value 0.77→0.41 versus 635/2.74 actual. Retained known power is poorly represented and finite-suspension opportunity is still absent. Basabe, Apostel and Grullón do not return; those marginal peers do not establish an appropriate suspended-star penalty.

Origin-selected peers: Luis Alexander Basabe (age 25, MLB/AAA/AA PA 0/26.0/0.0, draft None/unknown; actual 0 PA/0.000 wins); Sherten Apostel (age 23, MLB/AAA/AA PA 0/77.0/0.0, draft None/unknown; actual 0 PA/0.000 wins); Deivy Grullón (age 26, MLB/AAA/AA PA 0/63.0/0.0, draft None/unknown; actual 0 PA/0.000 wins).

Profile support: all=25 distinct people; active=14 distinct people.

## Yordan Alvarez: 2024 to 2025

Selection: largest gain.

Age 27; draft pick None, class unknown; captured listing 1 is soft. Full actual model features and saved fit are in cases.json; no individual target count/environment enters forecast inputs.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 561 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 35 | 95 | 53 |

Each logit is log(origin league probability) + fitted linear effect; softmax gives eight probabilities summing to one. Other is the anchored category.

| Event | Origin league probability | Linear odds effect | Forecast probability | Actual next count | Batting wins/600 contribution |
|---|---:|---:|---:|---:|---:|
| other | 0.465823 | 0.00000 | 0.469768 | 98 | 0.00000 |
| K | 0.225800 | -0.21821 | 0.183070 | 33 | -0.00000 |
| UBB | 0.079036 | 0.24862 | 0.102202 | 23 | 0.80696 |
| HBP | 0.011072 | -0.00141 | 0.011150 | 0 | 0.00284 |
| 1B | 0.141968 | 0.00781 | 0.144294 | 31 | 0.10263 |
| 2B | 0.042593 | 0.07228 | 0.046173 | 8 | 0.22243 |
| 3B | 0.003820 | -0.13932 | 0.003352 | 0 | -0.03671 |
| HR | 0.029888 | 0.28281 | 0.039992 | 6 | 1.01081 |

The contribution column uses existing neutral event values divided by wOBA scale and ten runs/win; sum equals the predicted batting rate. K/other affect other probabilities but have zero direct wOBA weight.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 584.774 | 3.70970 | 5.44249 |
| event | 584.774 | 2.10895 | 3.88236 |
| Actual | 199 | 0.91965 | 0.92510 |

Final product: fixed PA × (rate/600 + origin replacement 0.0031242). Saved numerical fit: {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 176, 'objective': 1.4672341460847973, 'maximum_gradient': 9.639855797945422e-07}; 1545 distinct active training people.

Largest actual linear-effect terms (columns K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| pooled_MLB_pa | 2.28067 | -0.05453, 0.16218, -0.02574, -0.01180, 0.13092, -0.09200, 0.38511 |
| pooled_MLB_K | -0.56205 | -0.30173, -0.10737, -0.06683, 0.01514, -0.03723, -0.01113, -0.19467 |
| intercept | 1.00000 | 0.27975, 0.00530, 0.03940, -0.00376, -0.01876, 0.10519, -0.14699 |
| pooled_MLB_BB | 0.24604 | 0.02930, 0.19309, 0.00716, -0.01998, 0.00246, -0.01343, 0.03179 |
| pooled_MLB_HR | 0.27886 | 0.01972, 0.02460, 0.01221, -0.03218, 0.02133, -0.02109, 0.14016 |
| position_10 | 1.00000 | -0.01857, 0.03724, -0.00330, 0.02185, 0.00034, -0.03572, 0.09814 |
| prior_debut | 1.00000 | -0.07972, -0.03063, -0.00634, -0.02205, 0.01195, -0.00408, -0.00228 |
| draft_class_unknown | 1.00000 | -0.02765, -0.01772, 0.04592, 0.01044, -0.02638, -0.01583, -0.04102 |
| elapsed_scaled | 0.50000 | 0.00179, -0.00540, -0.03414, 0.00676, -0.00792, -0.03818, 0.02133 |
| on_40man | 1.00000 | -0.03482, -0.02396, 0.03539, -0.00195, -0.00610, -0.00168, 0.01749 |
| pooled_MLB_BABIP | 0.13178 | 0.00130, 0.00174, 0.00616, 0.03265, 0.01048, 0.01175, -0.01793 |
| career_mlb_observed_pa | 0.44467 | -0.01873, -0.00831, -0.02191, 0.01747, -0.00319, -0.02312, 0.01186 |

Largest gain comes from reducing a false high: old rate 3.71→new 2.11, value 5.44→3.88 versus 199/0.93 actual. Strong prior 635/496/561 PA and 35/31/37 HR support good talent, and the model did not forecast the later absence because workload is unchanged. This gain partly rewards conservative compression during a future event. Soto, Ohtani and Guerrero stay productive, so this does not validate downgrading every elite hitter.

Origin-selected peers: Juan Soto (age 25, MLB/AAA/AA PA 713/0.0/0.0, draft None/unknown; actual 715 PA/6.406 wins); Shohei Ohtani (age 29, MLB/AAA/AA PA 731/0.0/0.0, draft None/unknown; actual 727 PA/7.877 wins); Vladimir Guerrero Jr. (age 25, MLB/AAA/AA PA 697/0.0/0.0, draft None/unknown; actual 680 PA/4.973 wins).

Profile support: all=439 distinct people; active=346 distinct people.

## Chris Davis: 2017 to 2018

Selection: false high.

Age 31; draft pick 148, class unknown; captured listing 1 is soft. Full actual model features and saved fit are in cases.json; no individual target count/environment enters forecast inputs.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2015 | MLB | 670 | 47 | 208 | 78 |
| 2016 | MLB | 665 | 38 | 219 | 85 |
| 2017 | A | 4 | 0 | 1 | 0 |
| 2017 | Aplus | 5 | 0 | 2 | 1 |
| 2017 | MLB | 524 | 26 | 195 | 57 |

Each logit is log(origin league probability) + fitted linear effect; softmax gives eight probabilities summing to one. Other is the anchored category.

| Event | Origin league probability | Linear odds effect | Forecast probability | Actual next count | Batting wins/600 contribution |
|---|---:|---:|---:|---:|---:|
| other | 0.466035 | 0.00000 | 0.350684 | 205 | -0.00000 |
| K | 0.216433 | 0.62607 | 0.304593 | 192 | 0.00000 |
| UBB | 0.080191 | 0.71689 | 0.123584 | 39 | 1.51152 |
| HBP | 0.009515 | 0.36602 | 0.010324 | 7 | 0.02940 |
| 1B | 0.145271 | -0.02193 | 0.106943 | 51 | -1.69171 |
| 2B | 0.045317 | 0.19564 | 0.041469 | 12 | -0.23906 |
| 3B | 0.004290 | -0.33556 | 0.002308 | 0 | -0.15525 |
| HR | 0.032947 | 0.88538 | 0.060094 | 16 | 2.71561 |

The contribution column uses existing neutral event values divided by wOBA scale and ten runs/win; sum equals the predicted batting rate. K/other affect other probabilities but have zero direct wOBA weight.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 493.395 | 1.17358 | 2.48283 |
| event | 493.395 | 2.17052 | 3.30265 |
| Actual | 522 | -3.68156 | -1.59518 |

Final product: fixed PA × (rate/600 + origin replacement 0.0030762). Saved numerical fit: {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 176, 'objective': 1.4524843271747951, 'maximum_gradient': 9.374748554196996e-07}; 946 distinct active training people.

Largest actual linear-effect terms (columns K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| pooled_MLB_K | 1.02478 | 0.56880, 0.21322, 0.20473, -0.01121, 0.08601, -0.01280, 0.38714 |
| pooled_MLB_pa | 2.43000 | -0.05507, 0.12837, -0.02111, 0.04200, 0.11581, -0.08536, 0.34775 |
| intercept | 1.00000 | 0.33494, 0.05703, 0.10527, -0.05176, 0.00580, 0.13488, -0.05660 |
| pooled_MLB_BB | 0.35404 | 0.03567, 0.27952, 0.02405, -0.03814, 0.01411, -0.01492, 0.04887 |
| position_3 | 1.00000 | -0.00237, 0.04324, -0.01591, 0.02408, 0.03684, -0.14262, 0.14366 |
| pooled_MLB_HR | 0.26226 | 0.02827, 0.01808, 0.01423, -0.03342, 0.02287, -0.02686, 0.13387 |
| age_centered | 0.80000 | -0.01078, -0.00916, 0.05658, -0.02599, -0.03843, -0.08841, -0.11328 |
| draft_class_unknown | 1.00000 | -0.03916, -0.03164, 0.05621, 0.00935, -0.04641, -0.02982, -0.07058 |
| career_mlb_observed_pa | 0.78350 | -0.06233, 0.00124, -0.05037, 0.03101, -0.00601, -0.02851, -0.01630 |
| elapsed_scaled | 0.90000 | -0.03995, -0.03090, -0.06176, 0.03497, 0.01259, -0.05965, 0.03253 |
| draft_elapsed | 1.00000 | -0.06120, 0.00004, 0.00750, 0.05729, -0.01210, 0.00376, -0.03306 |
| on_40man | 1.00000 | -0.05820, -0.01984, 0.02060, -0.00533, 0.00480, -0.01883, 0.01530 |

Largest false high. The recent 524-PA/26-HR/195-K season follows strong older power years. The joint logit uses positive cross-effects of K on HR and predicts 6.01% HR, raising rate 1.17→2.17 and value 2.48→3.30 versus actual 522 PA/−1.60 value and 16 HR. A later severe decline is uncertain, but raising power despite the declining source trajectory is a harmful learned mapping. Thames, Cozart and Duda provide less extreme subsequent results. This and Judge's power suppression show that physically coherent events are not enough.

Origin-selected peers: Eric Thames (age 30, MLB/AAA/AA PA 551/0.0/0.0, draft 219/unknown; actual 278 PA/1.145 wins); Zack Cozart (age 31, MLB/AAA/AA PA 507/0.0/0.0, draft 79/unknown; actual 253 PA/0.311 wins); Lucas Duda (age 31, MLB/AAA/AA PA 491/0.0/0.0, draft 243/unknown; actual 367 PA/1.188 wins).

Profile support: all=39 distinct people; active=28 distinct people.

## Ketel Marte: 2016 to 2017

Selection: ordinary.

Age 22; draft pick None, class unknown; captured listing 1 is soft. Full actual model features and saved fit are in cases.json; no individual target count/environment enters forecast inputs.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2014 | AA | 472 | 2 | 65 | 18 |
| 2014 | AAA | 90 | 2 | 13 | 8 |
| 2015 | AA | 8 | 0 | 0 | 1 |
| 2015 | AAA | 287 | 3 | 32 | 20 |
| 2015 | MLB | 247 | 2 | 43 | 24 |
| 2015 | RK121 | 3 | 0 | 0 | 0 |
| 2016 | AAA | 31 | 0 | 1 | 2 |
| 2016 | Aminus | 7 | 1 | 0 | 0 |
| 2016 | MLB | 466 | 1 | 84 | 18 |

Each logit is log(origin league probability) + fitted linear effect; softmax gives eight probabilities summing to one. Other is the anchored category.

| Event | Origin league probability | Linear odds effect | Forecast probability | Actual next count | Batting wins/600 contribution |
|---|---:|---:|---:|---:|---:|
| other | 0.474130 | 0.00000 | 0.524257 | 133 | 0.00000 |
| K | 0.211193 | -0.35374 | 0.163946 | 37 | -0.00000 |
| UBB | 0.076693 | -0.52553 | 0.050138 | 26 | -0.92499 |
| HBP | 0.008945 | -0.26378 | 0.007597 | 1 | -0.04894 |
| 1B | 0.149198 | 0.11843 | 0.185714 | 40 | 1.61172 |
| 2B | 0.044718 | -0.13863 | 0.043045 | 11 | -0.10394 |
| 3B | 0.004730 | 0.28351 | 0.006944 | 2 | 0.17341 |
| HR | 0.030393 | -0.60459 | 0.018359 | 5 | -1.20381 |

The contribution column uses existing neutral event values divided by wOBA scale and ten runs/win; sum equals the predicted batting rate. K/other affect other probabilities but have zero direct wOBA weight.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 323.886 | -1.25107 | 0.32485 |
| event | 323.886 | -0.49655 | 0.73215 |
| Actual | 255 | -0.12479 | 0.73139 |

Final product: fixed PA × (rate/600 + origin replacement 0.0030881). Saved numerical fit: {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 173, 'objective': 1.444610428795721, 'maximum_gradient': 8.727607887749581e-07}; 866 distinct active training people.

Largest actual linear-effect terms (columns K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.32042, 0.15988, 0.05978, -0.03773, 0.02600, 0.14809, -0.03640 |
| pooled_MLB_K | -0.44825 | -0.26544, -0.09675, -0.06783, 0.01638, -0.03480, 0.00201, -0.17458 |
| pooled_AAA_K | -0.91553 | -0.13949, -0.09248, -0.07540, 0.00937, -0.08005, 0.00952, -0.21352 |
| position_6 | 1.00000 | -0.04723, -0.08983, -0.13016, -0.00748, -0.04879, 0.05664, -0.20615 |
| pooled_MLB_pa | 1.10600 | -0.02559, 0.04334, 0.00356, 0.01194, 0.06608, -0.04479, 0.18011 |
| pooled_MLB_BB | -0.20807 | -0.02519, -0.16121, -0.00996, 0.01761, -0.00922, 0.00963, -0.02017 |
| age_centered | -1.00000 | 0.00862, -0.00724, -0.03209, 0.03219, 0.05545, 0.12063, 0.14718 |
| pooled_MLB_HR | -0.22666 | -0.01832, -0.01240, -0.01352, 0.02394, -0.02317, 0.02109, -0.11717 |
| pooled_AA_K | -0.70862 | -0.10352, -0.07411, -0.05081, -0.03292, -0.02708, 0.01469, -0.05631 |
| draft_class_unknown | 1.00000 | -0.04279, -0.07593, 0.05340, 0.01732, -0.06762, -0.04228, -0.07564 |
| pooled_AA_BB | -0.29692 | 0.01365, -0.06687, 0.00888, 0.01156, -0.00471, 0.00847, -0.00947 |
| age_squared | 1.00000 | -0.00338, -0.01471, -0.02206, -0.00945, -0.00964, -0.04790, 0.03738 |

Ordinary case. A low-power/contact profile from 466 current MLB PA/1 HR/84 K and 247 prior MLB PA is preserved alongside long minor records. Predicted K 16.4% and singles 18.6% offset low walks/power; rate improves −1.251→−0.497 toward actual −0.125. Fixed PA 324 versus actual 255 makes expected value 0.732 almost exactly actual 0.731. The value agreement partly offsets rate and workload errors; it is not proof all components are right. Garcia, Perez and Kepler have varied next seasons.

Origin-selected peers: Avisaíl García (age 25, MLB/AAA/AA PA 453/14.0/0.0, draft None/unknown; actual 561 PA/4.288 wins); Hernán Pérez (age 25, MLB/AAA/AA PA 430/67.0/0.0, draft None/unknown; actual 458 PA/0.584 wins); Max Kepler (age 23, MLB/AAA/AA PA 447/128.0/0.0, draft None/unknown; actual 568 PA/1.543 wins).

Profile support: all=112 distinct people; active=96 distinct people.

## Decision

Do not adopt this naked event-logit model. Proper count likelihood improves over a league-only null, but batting rate/value regress and elite power is implausibly compressed. The exact specification is rejected, not coherent component forecasting as a family. Preserve all negative evidence and V33b/V34 controls.

Next bounded hypothesis: give the event model a direct empirical own-MLB-count anchor, then learn residual adjustments instead of reconstructing established batting from scratch. Keep the same conditional likelihood/settings/context and fixed workload; do not silently retune the penalty or famous-player outcomes.
