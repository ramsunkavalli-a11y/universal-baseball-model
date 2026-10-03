# V41: completed future-MLB contact player review

Same 30,506 historical rows, whole-player chronological folds, V34 workload and replacement rates. Conditional batting rate and delivered batting-plus-replacement are distinct. No protected 2026 outcomes. Sixty rate heads replay; 7,625 unsupported rows retain the exact baseline.

Coefficient/tree-path accounting exactly reconstructs each fitted rate. It is not a causal contact effect, SHAP or a fixed-input ablation; refitting changes the old feature mapping. The histogram candidate also changes architecture versus the ridge benchmark, so its loss cannot be attributed solely to contact. Source-measurement equivalence across levels remains uncertain. Origin-selected peers include later unsuccessful players.

## Aaron Judge: 2016 → 2017

Selection: Fixed case.

Age 24.0; stage Current MLB; source position 9; draft pick 32; contact-supported application False.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2014 | A | 278 | 59 | 38 | 9 |
| 2014 | Aplus | 285 | 72 | 49 | 8 |
| 2015 | AA | 280 | 70 | 23 | 12 |
| 2015 | AAA | 260 | 74 | 29 | 8 |
| 2016 | AAA | 410 | 98 | 47 | 19 |
| 2016 | MLB | 95 | 42 | 9 | 4 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| AAA | 257.000 | 0.41586 | 0.07283 | 0.32213 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 143.966 | -0.05720 | 0.43085 |
| contact_ridge | 143.966 | -0.05720 | 0.43085 |
| contact_hist | 143.966 | -0.05720 | 0.43085 |
| Actual | 678 | 5.32988 | 8.10841 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00308809). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.74635; reconstructed rate -0.05720.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| age_centered | -0.600000 | 0.286822 |
| draft_class_unknown | 1.000000 | -0.204214 |
| position_9 | 1.000000 | 0.165561 |
| pooled_mlb_quality | -0.175091 | -0.119076 |
| pooled_Aplus_BB | 0.580074 | 0.113202 |
| pooled_Aplus_BABIP | 0.367983 | 0.090674 |
| work_0 | 95.078254 | 0.083463 |
| AA_1_pa | 0.466667 | -0.078361 |
| quality_0 | -0.175091 | -0.075280 |
| pooled_A_BB | 0.354423 | 0.070655 |
| pooled_AA_BABIP | 0.260135 | 0.065423 |
| prior_debut | 1.000000 | 0.064258 |

contact_ridge: exact -0.05720 baseline fallback — No observed bucket with actual active-player training support.

contact_hist: exact -0.05720 baseline fallback — No observed bucket with actual active-player training support.

Both arms are exact fallbacks: minor shape exists, but no earlier contact-bearing training history exists. The baseline misses both first-year opportunity (144 versus 678 PA) and his offensive breakout. His 410 AAA PA/19 HR and poor 95-PA MLB debut are present. This is not evidence that reconstructed 2016 shape failed to predict his breakout; it was never allowed to do so. The weaker origin-selected debut peers demonstrate why retrospectively treating every brief debut as Judge would be wrong.

Origin-selected peers: Jaff Decker (origin MLB/AAA/AA PA 57/417.0/0.0; expected/actual MLB PA 36.3/62; baseline/ridge/tree rate -0.623/-0.623/-0.623; actual batting rate -2.957); Deven Marrero (origin MLB/AAA/AA PA 14/388.0/0.0; expected/actual MLB PA 58.0/188; baseline/ridge/tree rate -1.283/-1.283/-1.283; actual batting rate -3.272); Kaleb Cowart (origin MLB/AAA/AA PA 87/458.0/0.0; expected/actual MLB PA 178.7/117; baseline/ridge/tree rate -0.895/-0.895/-0.895; actual batting rate -1.217).

## Aaron Judge: 2024 → 2025

Selection: Fixed case; contact_hist largest value harm.

Age 32.0; stage Current MLB; source position 8; draft pick 32; contact-supported application True.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 696 | 175 | 92 | 62 |
| 2023 | MLB | 458 | 130 | 79 | 37 |
| 2024 | MLB | 704 | 171 | 113 | 58 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| MLB | 807.400 | 0.54261 | 0.08574 | 0.32973 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 548.496 | 4.55334 | 5.87607 |
| contact_ridge | 548.496 | 4.67756 | 5.98962 |
| contact_hist | 548.496 | 3.38717 | 4.81000 |
| Actual | 679 | 6.28743 | 9.23105 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00312416). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.91248; reconstructed rate 4.55334.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 3.648566 | 2.685922 |
| quality_0 | 2.794425 | 1.297297 |
| work_0 | 704.289831 | 0.841611 |
| age_centered | 1.000000 | -0.558514 |
| quality_2 | 2.408333 | 0.477308 |
| work_2 | 696.000000 | 0.414097 |
| quality_1 | 1.317130 | 0.285426 |
| reorganized | 1.000000 | -0.276917 |
| work_1 | 458.000000 | 0.231390 |
| pooled_MLB_BB | 0.707557 | 0.193396 |
| pooled_MLB_pa | 2.480000 | -0.193361 |
| prior_debut | 1.000000 | 0.156958 |

contact_ridge: reference -0.90035; reconstructed rate 4.67756.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 3.648566 | 2.646473 |
| quality_0 | 2.794425 | 1.291631 |
| work_0 | 704.289831 | 0.805125 |
| age_centered | 1.000000 | -0.563224 |
| quality_2 | 2.408333 | 0.500739 |
| work_2 | 696.000000 | 0.370407 |
| reorganized | 1.000000 | -0.329173 |
| quality_1 | 1.317130 | 0.297517 |
| work_1 | 458.000000 | 0.208776 |
| pooled_MLB_BB | 0.707557 | 0.184922 |
| prior_debut | 1.000000 | 0.155258 |
| pooled_MLB_pa | 2.480000 | -0.151323 |

contact_hist: reference -0.32160; reconstructed rate 3.38717.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 3.648566 | 2.282917 |
| quality_0 | 2.794425 | 0.517472 |
| quality_2 | 2.408333 | 0.354257 |
| pooled_MLB_BB | 0.150756 | 0.231402 |
| age_centered | 1.000000 | -0.227379 |
| pooled_MLB_HR | 0.080479 | 0.151988 |
| quality_1 | 1.317130 | 0.086742 |
| pooled_MLB_pa | 1488.000000 | 0.084741 |
| work_0 | 704.289831 | 0.073339 |
| pooled_MLB_BABIP | 0.338435 | -0.055524 |
| pooled_MLB_3B | 0.000945 | -0.036125 |
| shape_MLB_OPPO_GB | 0.039233 | 0.033923 |

Ridge modestly raises established batting from 4.553 to 4.678 wins/600, closer to realized 6.287. The tree compresses it to 3.387 despite 58 HR in 704 PA and substantial MLB contact. Its paths remain dominated by the learned quality buckets and cannot extrapolate an extreme hitter as well as the linear rate head. The tree also changes the architecture, so its harm is not solely a causal contact-shape effect. Neither arm fixes the unchanged 548-PA forecast versus 679 actual.

Origin-selected peers: Nick Castellanos (origin MLB/AAA/AA PA 659/0.0/0.0; expected/actual MLB PA 529.0/589; baseline/ridge/tree rate 0.068/0.080/0.156; actual batting rate -0.536); Matt Olson (origin MLB/AAA/AA PA 685/0.0/0.0; expected/actual MLB PA 629.9/724; baseline/ridge/tree rate 2.006/2.039/1.859; actual batting rate 2.703); Matt Chapman (origin MLB/AAA/AA PA 647/0.0/0.0; expected/actual MLB PA 516.8/535; baseline/ridge/tree rate 0.634/0.636/0.478; actual batting rate 1.227).

## Masyn Winn: 2023 → 2024

Selection: Fixed case.

Age 21.0; stage Current MLB; source position 6; draft pick 54; contact-supported application True.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | A | 284 | 60 | 40 | 3 |
| 2021 | Aplus | 154 | 40 | 6 | 2 |
| 2022 | AA | 403 | 86 | 50 | 11 |
| 2022 | Aplus | 147 | 29 | 13 | 1 |
| 2023 | AAA | 498 | 83 | 44 | 18 |
| 2023 | MLB | 137 | 26 | 10 | 2 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| MLB | 95.000 | 0.69343 | 0.07179 | 0.38974 |
| AAA | 362.000 | 0.72691 | 0.06277 | 0.37662 |
| AA | 209.600 | 0.65012 | 0.08140 | 0.38372 |
| Aplus | 145.400 | 0.69238 | 0.07172 | 0.39772 |
| A | 107.400 | 0.63028 | 0.06268 | 0.35583 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 305.512 | -0.79671 | 0.54021 |
| contact_ridge | 305.512 | -0.90115 | 0.48704 |
| contact_hist | 305.512 | -1.32511 | 0.27116 |
| Actual | 637 | 0.25454 | 2.25951 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00309608). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.90048; reconstructed rate -0.79671.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| age_centered | -1.200000 | 0.690419 |
| pooled_mlb_quality | -0.557599 | -0.419389 |
| position_6 | 1.000000 | -0.273235 |
| quality_0 | -0.557599 | -0.256150 |
| work_0 | 137.000000 | 0.205346 |
| reorganized | 1.000000 | -0.196306 |
| pooled_MLB_BABIP | -0.512690 | 0.123036 |
| prior_debut | 1.000000 | 0.110667 |
| pooled_A_BB | 0.383432 | 0.108512 |
| age_squared | 1.440000 | 0.106041 |
| AA_1_pa | 0.671667 | -0.101883 |
| pooled_Aplus_BABIP | 0.368679 | 0.088302 |

contact_ridge: reference -0.88863; reconstructed rate -0.90115.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| age_centered | -1.200000 | 0.694700 |
| pooled_mlb_quality | -0.557599 | -0.412520 |
| reorganized | 1.000000 | -0.296115 |
| position_6 | 1.000000 | -0.274979 |
| quality_0 | -0.557599 | -0.258097 |
| work_0 | 137.000000 | 0.190943 |
| pooled_MLB_BABIP | -0.512690 | 0.118676 |
| AA_1_pa | 0.671667 | -0.109825 |
| pooled_A_BB | 0.383432 | 0.108926 |
| age_squared | 1.440000 | 0.104377 |
| prior_debut | 1.000000 | 0.097902 |
| shape_AA_available | 1.000000 | -0.094726 |

contact_hist: reference -0.30573; reconstructed rate -1.32511.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | -0.557599 | -0.605825 |
| pooled_Aplus_HR | 0.016129 | -0.366760 |
| age_centered | -1.200000 | 0.314768 |
| pooled_A_BB | 0.118343 | 0.179244 |
| pooled_AAA_HR | 0.035117 | 0.158155 |
| shape_Aplus_CENTER_LD | 0.081500 | -0.154347 |
| shape_AAA_PULL_LD | 0.082251 | -0.141670 |
| shape_MLB_coverage | 0.693431 | -0.127438 |
| pooled_A_2B | 0.051775 | 0.112937 |
| position_6 | 1.000000 | -0.095972 |
| pooled_MLB_BABIP | 0.248731 | 0.083066 |
| pooled_AAA_pa | 498.000000 | -0.082918 |

Both new rates worsen (-0.797 to -0.901/-1.325 versus +0.255 realized). His 498 AAA PA/18 HR/83 K remain alongside 137 MLB PA/26 K; distinct levels and contact shrinkage did not undo the overly pessimistic early-MLB translation. The tree's lower-level HR and pooled MLB-quality paths account for much of its pessimism. Edwards and Meadows succeeded more than Ornelas, so a broad cohort improvement must retain that dispersion rather than adjust Winn alone.

Origin-selected peers: Xavier Edwards (origin MLB/AAA/AA PA 84/433.0/0.0; expected/actual MLB PA 162.4/303; baseline/ridge/tree rate -0.836/-0.882/-1.409; actual batting rate 2.456); Parker Meadows (origin MLB/AAA/AA PA 145/517.0/0.0; expected/actual MLB PA 213.1/298; baseline/ridge/tree rate -0.864/-0.896/0.211; actual batting rate 0.564); Jonathan Ornelas (origin MLB/AAA/AA PA 8/517.0/0.0; expected/actual MLB PA 50.6/40; baseline/ridge/tree rate -0.824/-1.284/-1.319; actual batting rate -3.888).

## Spencer Steer: 2022 → 2023

Selection: Fixed case.

Age 24.0; stage Current MLB; source position 5; draft pick 90; contact-supported application True.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | AA | 280 | 73 | 19 | 14 |
| 2021 | Aplus | 208 | 32 | 35 | 10 |
| 2022 | AA | 156 | 23 | 14 | 8 |
| 2022 | AAA | 336 | 66 | 36 | 15 |
| 2022 | MLB | 108 | 26 | 11 | 2 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| MLB | 65.000 | 0.60185 | 0.07879 | 0.36364 |
| AAA | 225.000 | 0.66964 | 0.09231 | 0.40000 |
| AA | 261.400 | 0.68789 | 0.12120 | 0.30825 |
| Aplus | 108.800 | 0.65385 | 0.12452 | 0.27778 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 180.375 | -0.23663 | 0.49361 |
| contact_ridge | 180.375 | -0.06450 | 0.54536 |
| contact_hist | 180.375 | -0.18162 | 0.51015 |
| Actual | 665 | 1.90921 | 4.17493 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00313097). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.85147; reconstructed rate -0.23663.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| age_centered | -0.600000 | 0.339709 |
| work_0 | 108.000000 | 0.157405 |
| reorganized | 1.000000 | -0.138872 |
| draft_class_unknown | 1.000000 | -0.124039 |
| position_5 | 1.000000 | 0.116508 |
| prior_debut | 1.000000 | 0.086178 |
| pooled_AA_HR | 0.162500 | 0.078378 |
| pooled_AAA_HR | 0.112844 | 0.075201 |
| pooled_AAA_BB | 0.209174 | 0.070103 |
| pooled_Aplus_BB | 0.551351 | 0.068550 |
| pooled_mlb_quality | -0.084424 | -0.063258 |
| pooled_AA_pa | 0.633333 | -0.053040 |

contact_ridge: reference -0.89124; reconstructed rate -0.06450.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| age_centered | -0.600000 | 0.335946 |
| reorganized | 1.000000 | -0.170906 |
| work_0 | 108.000000 | 0.154041 |
| draft_class_unknown | 1.000000 | -0.126197 |
| position_5 | 1.000000 | 0.115320 |
| shape_AAA_PULL_GB | 1.815385 | -0.098785 |
| prior_debut | 1.000000 | 0.086797 |
| shape_Aplus_coverage | 0.653846 | 0.084557 |
| shape_MLB_available | 1.000000 | -0.081266 |
| shape_AA_available | 1.000000 | -0.078439 |
| pooled_AA_HR | 0.162500 | 0.075859 |
| pooled_AAA_HR | 0.112844 | 0.072097 |

contact_hist: reference -0.28675; reconstructed rate -0.18162.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_AAA_HR | 0.041284 | 0.459913 |
| pooled_AA_HR | 0.046250 | 0.298275 |
| pooled_mlb_quality | -0.084424 | -0.238733 |
| reorganized | 1.000000 | -0.100285 |
| shape_Aplus_PULL_LD | 0.090038 | -0.083736 |
| pooled_Aplus_2B | 0.039790 | -0.071835 |
| work_0 | 108.000000 | -0.068671 |
| age_centered | -0.600000 | 0.068619 |
| pooled_AAA_BB | 0.100917 | 0.059212 |
| pooled_AAA_BABIP | 0.289389 | -0.058868 |
| position_2 | 0.000000 | 0.046522 |
| shape_AAA_PULL_LD | 0.073846 | -0.046171 |

Ridge slightly improves batting (-0.237 to -0.064 versus +1.909); the tree only reaches -0.182. His 23 combined AA/AAA HR, minor strikeout control and 108-PA MLB debut are recorded. The tree credits AAA/AA power but discounts pooled MLB quality. The unchanged 180 expected PA versus 665 actual is the much larger opportunity miss. Henderson succeeded while Freeman/Brennan were weaker hitters: favorable minor production is not a guarantee of a strong debut.

Origin-selected peers: Tyler Freeman (origin MLB/AAA/AA PA 86/343.0/0.0; expected/actual MLB PA 186.2/168; baseline/ridge/tree rate -0.861/-1.012/-1.200; actual batting rate -1.522); Gunnar Henderson (origin MLB/AAA/AA PA 132/295.0/208.0; expected/actual MLB PA 392.5/622; baseline/ridge/tree rate 0.508/0.519/0.990; actual batting rate 1.424); Will Brennan (origin MLB/AAA/AA PA 45/433.0/157.0; expected/actual MLB PA 242.3/455; baseline/ridge/tree rate -0.482/-0.727/-0.496; actual batting rate -1.639).

## Nick Kurtz: 2024 → 2025

Selection: Fixed case.

Age 21.0; stage Upper minors; source position 3; draft pick 4; contact-supported application True.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 7 | 10 | 4 |
| 2024 | AA | 15 | 3 | 2 | 0 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| AA | 10.000 | 0.66667 | 0.09091 | 0.33636 |
| A | 18.000 | 0.51429 | 0.10169 | 0.31356 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 42.495 | -0.13556 | 0.12316 |
| contact_ridge | 42.495 | -0.15712 | 0.12163 |
| contact_hist | 42.495 | -0.51441 | 0.09633 |
| Actual | 489 | 5.15001 | 5.72099 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00312416). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.97229; reconstructed rate -0.13556.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| age_centered | -1.200000 | 0.642920 |
| reorganized | 1.000000 | -0.276479 |
| draft_rank | 0.817615 | 0.160851 |
| position_3 | 1.000000 | 0.133637 |
| draft_known | 1.000000 | -0.089751 |
| age_squared | 1.440000 | 0.088090 |
| draft_college | 1.000000 | 0.073031 |
| pooled_A_BB | 0.533333 | 0.063729 |
| absence_window_scaled | 1.000000 | -0.055394 |
| pooled_A_BABIP | 0.157895 | 0.031379 |
| pooled_AA_BABIP | 0.090909 | 0.029480 |
| pooled_AA_BB | 0.069565 | 0.022402 |

contact_ridge: reference -0.94934; reconstructed rate -0.15712.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| age_centered | -1.200000 | 0.654417 |
| reorganized | 1.000000 | -0.353218 |
| draft_rank | 0.817615 | 0.149361 |
| position_3 | 1.000000 | 0.136528 |
| draft_known | 1.000000 | -0.097066 |
| age_squared | 1.440000 | 0.092008 |
| draft_college | 1.000000 | 0.083639 |
| shape_AA_available | 1.000000 | -0.062778 |
| pooled_A_BB | 0.533333 | 0.060970 |
| shape_A_available | 1.000000 | 0.054125 |
| absence_window_scaled | 1.000000 | -0.046605 |
| shape_AA_coverage | 0.666667 | 0.042400 |

contact_hist: reference -0.33086; reconstructed rate -0.51441.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 0.000000 | -0.262411 |
| age_centered | -1.200000 | 0.183155 |
| reorganized | 1.000000 | -0.100951 |
| pooled_AAA_HR | 0.030000 | 0.077746 |
| pooled_A_BB | 0.133333 | 0.065653 |
| draft_rank | 0.817615 | 0.065536 |
| position_2 | 0.000000 | 0.063609 |
| work_0 | 0.000000 | -0.052516 |
| career_mlb_observed_pa | 0.000000 | -0.049174 |
| shape_AA_OPPO_OFFB | 0.090909 | -0.046363 |
| pooled_MLB_HR | 0.030000 | -0.043949 |
| A_0_pa | 35.000000 | -0.034438 |

Only 50 official professional PA and 28 measured contacts exist. Both new rates become slightly more pessimistic while the fixed model expects only 42 PA versus 489 realized. The tree follows population quality/age and stabilized minor event rates; sparse shape cannot reveal a future 5.150-win/600 batting season. Draft pick four is present but weakly translated by this model. Non-arriving Johnson/Montgomery/Jenkins peers prevent retrospective replacement with an unconditional success assumption. This remains a fast-entry/high-pedigree talent-and-opportunity gap, not a contact-data solution.

Origin-selected peers: Benny Montgomery (origin MLB/AAA/AA PA 0/0.0/48.0; expected/actual MLB PA 37.2/0; baseline/ridge/tree rate -0.240/-0.619/0.116; no future MLB PA; no observed batting rate); Termarr Johnson (origin MLB/AAA/AA PA 0/0.0/57.0; expected/actual MLB PA 26.9/0; baseline/ridge/tree rate -0.300/-0.700/-0.725; no future MLB PA; no observed batting rate); Walker Jenkins (origin MLB/AAA/AA PA 0/0.0/28.0; expected/actual MLB PA 44.8/0; baseline/ridge/tree rate 0.088/0.046/-0.766; no future MLB PA; no observed batting rate).

## Gavin Lux: 2023 → 2024

Selection: Fixed case.

Age 25.0; stage Inactive / unknown; source position 4; draft pick 20; contact-supported application True.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 74 | 15 | 6 | 1 |
| 2021 | MLB | 381 | 83 | 38 | 7 |
| 2022 | MLB | 471 | 95 | 47 | 6 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| MLB | 408.000 | 0.67393 | 0.05551 | 0.45630 |
| AAA | 31.800 | 0.71622 | 0.08498 | 0.35053 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 215.427 | -0.23943 | 0.58101 |
| contact_ridge | 215.427 | -0.19152 | 0.59821 |
| contact_hist | 215.427 | -0.21777 | 0.58879 |
| Actual | 487 | 0.08394 | 1.58897 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00309608). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.90645; reconstructed rate -0.23943.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| work_2 | 381.156855 | 0.246301 |
| age_centered | -0.400000 | 0.228522 |
| work_1 | 471.000000 | 0.224776 |
| reorganized | 1.000000 | -0.206516 |
| prior_debut | 1.000000 | 0.175350 |
| position_4 | 1.000000 | -0.121516 |
| pooled_mlb_quality | 0.150719 | 0.111474 |
| draft_rank | 0.605872 | 0.108091 |
| quality_present_1 | 1.000000 | 0.083927 |
| pooled_MLB_pa | 1.009000 | -0.076543 |
| draft_class_unknown | 1.000000 | -0.068901 |
| quality_present_2 | 1.000000 | -0.068676 |

contact_ridge: reference -0.92008; reconstructed rate -0.19152.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| work_2 | 381.156855 | 0.232107 |
| age_centered | -0.400000 | 0.230800 |
| reorganized | 1.000000 | -0.227397 |
| work_1 | 471.000000 | 0.210269 |
| prior_debut | 1.000000 | 0.167164 |
| position_4 | 1.000000 | -0.126959 |
| pooled_mlb_quality | 0.150719 | 0.109776 |
| draft_rank | 0.605872 | 0.103693 |
| quality_present_1 | 1.000000 | 0.081659 |
| shape_MLB_available | 1.000000 | -0.075046 |
| draft_class_unknown | 1.000000 | -0.071720 |
| draft_known | 1.000000 | -0.068589 |

contact_hist: reference -0.30596; reconstructed rate -0.21777.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| age_centered | -0.400000 | 0.158531 |
| shape_MLB_OPPO_OFFB | 0.075591 | -0.146277 |
| pooled_MLB_BB | 0.096966 | 0.138773 |
| pooled_AAA_HR | 0.024931 | -0.129400 |
| MLB_1_pa | 471.000000 | 0.087148 |
| draft_rank_low_exposure | 0.059052 | 0.084090 |
| pooled_MLB_BABIP | 0.320568 | -0.070826 |
| MLB_0_pa | 0.000000 | -0.064143 |
| pooled_AAA_2B | 0.051247 | -0.058436 |
| reorganized | 1.000000 | -0.055062 |
| position_2 | 0.000000 | 0.036158 |
| pooled_AA_HR | 0.030000 | 0.031854 |

Both rates move slightly closer to realized +0.084, using earlier MLB and minor contact despite no current PA. The tree has meaningful prior-MLB opposite-fly accounting, but historical work/age and batting counts remain important. Contribution improves only slightly because PA remains 215 versus 487. The origin-selected absent peers have no future MLB PA: Lux's return cannot justify assigning healthy full seasons to every absent player. Source data here do not diagnose injury severity.

Origin-selected peers: Nick Ciuffo (origin MLB/AAA/AA PA 0/0.0/0.0; expected/actual MLB PA 9.5/0; baseline/ridge/tree rate -1.256/-1.417/-1.326; no future MLB PA; no observed batting rate); Will Craig (origin MLB/AAA/AA PA 0/0.0/0.0; expected/actual MLB PA 5.9/0; baseline/ridge/tree rate -0.881/-0.956/-0.264; no future MLB PA; no observed batting rate); Nick Plummer (origin MLB/AAA/AA PA 0/0.0/0.0; expected/actual MLB PA 20.7/0; baseline/ridge/tree rate -0.237/-0.312/-0.811; no future MLB PA; no observed batting rate).

## Chase Meidroth: 2024 → 2025

Selection: Fixed case.

Age 22.0; stage Upper minors; source position 6; draft pick 129; contact-supported application True.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2022 | A | 85 | 9 | 12 | 4 |
| 2022 | RK124 | 11 | 2 | 2 | 0 |
| 2023 | AA | 396 | 78 | 59 | 7 |
| 2023 | Aplus | 97 | 20 | 21 | 2 |
| 2024 | AAA | 558 | 71 | 105 | 7 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| AAA | 371.000 | 0.66487 | 0.04883 | 0.45648 |
| AA | 198.400 | 0.62626 | 0.06836 | 0.44370 |
| Aplus | 43.200 | 0.55670 | 0.07542 | 0.38827 |
| A | 36.000 | 0.70588 | 0.07794 | 0.31765 |
| RK124 | 3.000 | 0.45455 | 0.09709 | 0.30874 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 40.360 | -0.33695 | 0.10343 |
| contact_ridge | 40.360 | -0.27368 | 0.10768 |
| contact_hist | 40.360 | -1.49727 | 0.02538 |
| Actual | 505 | -0.90862 | 0.80883 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00312416). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.91248; reconstructed rate -0.33695.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| age_centered | -1.000000 | 0.558514 |
| reorganized | 1.000000 | -0.276917 |
| position_6 | 1.000000 | -0.222118 |
| pooled_AAA_BB | 0.917325 | 0.216859 |
| draft_college | 1.000000 | 0.148810 |
| pooled_AA_BB | 0.524376 | 0.140258 |
| pooled_Aplus_BB | 0.596396 | 0.116529 |
| pooled_Aplus_BABIP | 0.418079 | 0.107188 |
| draft_known | 1.000000 | -0.090134 |
| AA_1_pa | 0.660000 | -0.087144 |
| draft_rank | 0.360627 | 0.085301 |
| pooled_AA_pa | 0.528000 | -0.084638 |

contact_ridge: reference -0.90035; reconstructed rate -0.27368.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| age_centered | -1.000000 | 0.563224 |
| reorganized | 1.000000 | -0.329173 |
| position_6 | 1.000000 | -0.218768 |
| pooled_AAA_BB | 0.917325 | 0.204823 |
| draft_college | 1.000000 | 0.158680 |
| pooled_AA_BB | 0.524376 | 0.138070 |
| shape_RK124_available | 1.000000 | 0.126495 |
| pooled_Aplus_BB | 0.596396 | 0.119555 |
| pooled_Aplus_BABIP | 0.418079 | 0.101937 |
| draft_known | 1.000000 | -0.095753 |
| AA_1_pa | 0.660000 | -0.091914 |
| pooled_AA_pa | 0.528000 | -0.084708 |

contact_hist: reference -0.32160; reconstructed rate -1.49727.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_AAA_HR | 0.015198 | -0.264916 |
| pooled_mlb_quality | 0.000000 | -0.203262 |
| shape_AA_OPPO_OFFB | 0.108579 | 0.176958 |
| pooled_AA_2B | 0.042706 | -0.140424 |
| shape_AAA_OPPO_GB | 0.144374 | -0.130996 |
| shape_Aplus_OPPO_OFFB | 0.081006 | -0.103453 |
| age_centered | -1.000000 | 0.101716 |
| pooled_AA_HR | 0.020633 | -0.092913 |
| reorganized | 1.000000 | -0.090859 |
| MLB_0_pa | 0.000000 | -0.089289 |
| pooled_Aplus_pa | 77.600000 | 0.087643 |
| shape_AAA_OPPO_OFFB | 0.076433 | -0.080479 |

Ridge moves away from his realized batting (-0.337 to -0.274 versus -0.909); the tree overshoots to -1.497 but is closer in conditional rate. The latter credits some AA contact and penalizes low AAA HR/opposite ground-ball patterns. With only 40 expected versus 505 actual PA, its contribution falls further from the observed positive batting-plus-replacement value. A better conditional rate is not enough when opportunity is wrong; most origin-selected peers also did not get comparable MLB use.

Origin-selected peers: Tristan Peters (origin MLB/AAA/AA PA 0/478.0/0.0; expected/actual MLB PA 42.5/12; baseline/ridge/tree rate -0.650/-0.857/-0.990; actual batting rate -15.495); Grant Lavigne (origin MLB/AAA/AA PA 0/530.0/0.0; expected/actual MLB PA 33.8/0; baseline/ridge/tree rate -0.809/-0.899/-0.620; no future MLB PA; no observed batting rate); Owen Caissie (origin MLB/AAA/AA PA 0/549.0/0.0; expected/actual MLB PA 166.7/27; baseline/ridge/tree rate 0.028/-0.033/0.594; actual batting rate -3.295).

## Cody Bellinger: 2016 → 2017

Selection: Fixed case.

Age 20.0; stage Upper minors; source position 3; draft pick 124; contact-supported application False.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2014 | RK128 | 233 | 40 | 15 | 3 |
| 2015 | Aplus | 544 | 150 | 51 | 30 |
| 2016 | AA | 465 | 94 | 57 | 23 |
| 2016 | AAA | 12 | 0 | 1 | 3 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| AAA | 11.000 | 0.91667 | 0.11712 | 0.28829 |
| AA | 300.000 | 0.64516 | 0.12250 | 0.28750 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 35.516 | 0.08471 | 0.11469 |
| contact_ridge | 35.516 | 0.08471 | 0.11469 |
| contact_hist | 35.516 | 0.08471 | 0.11469 |
| Actual | 548 | 2.70047 | 4.15217 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00308809). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.74635; reconstructed rate 0.08471.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| age_centered | -1.400000 | 0.669250 |
| draft_class_unknown | 1.000000 | -0.204214 |
| age_squared | 1.960000 | 0.149140 |
| position_3 | 1.000000 | 0.146736 |
| pooled_AA_pa | 0.775000 | -0.109214 |
| draft_known | 1.000000 | 0.062907 |
| pooled_AAA_HR | 0.235714 | 0.059513 |
| pooled_AA_BB | 0.350442 | 0.056458 |
| pooled_Aplus_K | 0.371898 | -0.042851 |
| pooled_AA_HR | 0.160177 | 0.038557 |
| pooled_Aplus_HR | 0.204484 | 0.026242 |
| pooled_AA_BABIP | -0.098446 | -0.024759 |

contact_ridge: exact 0.08471 baseline fallback — No observed bucket with actual active-player training support.

contact_hist: exact 0.08471 baseline fallback — No observed bucket with actual active-player training support.

Exact fallback is required, not an evaluated shape failure: available AA/AAA shape has no earlier supported training. The baseline's 35.5 PA and near-average conditional rate miss the realized 548 PA/+2.701 batting season. His 23 HR in 465 AA PA are already available. Contact reconstruction does not cure the first-year allocation problem or justify changing his correctly non-roster spring status by memory.

Origin-selected peers: Jamie Westbrook (origin MLB/AAA/AA PA 0/0.0/473.0; expected/actual MLB PA 10.0/0; baseline/ridge/tree rate -0.416/-0.416/-0.416; no future MLB PA; no observed batting rate); Kean Wong (origin MLB/AAA/AA PA 0/0.0/492.0; expected/actual MLB PA 20.3/0; baseline/ridge/tree rate -0.263/-0.263/-0.263; no future MLB PA; no observed batting rate); Isiah Kiner-Falefa (origin MLB/AAA/AA PA 0/0.0/457.0; expected/actual MLB PA 6.7/0; baseline/ridge/tree rate -0.135/-0.135/-0.135; no future MLB PA; no observed batting rate).

## J.D. Martinez: 2017 → 2018

Selection: contact_ridge largest value gain.

Age 29.0; stage Current MLB; source position 9; draft pick 611; contact-supported application True.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2015 | MLB | 657 | 178 | 46 | 38 |
| 2016 | AAA | 38 | 11 | 1 | 0 |
| 2016 | MLB | 517 | 128 | 47 | 22 |
| 2017 | AAA | 18 | 6 | 2 | 1 |
| 2017 | Aplus | 8 | 1 | 0 | 1 |
| 2017 | MLB | 489 | 128 | 45 | 45 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| AAA | 30.000 | 0.61983 | 0.08462 | 0.29538 |
| Aplus | 7.000 | 0.87500 | 0.09346 | 0.29907 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 474.787 | 3.23769 | 4.02255 |
| contact_ridge | 474.787 | 3.55580 | 4.27428 |
| contact_hist | 474.787 | 3.16450 | 3.96464 |
| Actual | 649 | 5.37887 | 7.81709 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00307618). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.77390; reconstructed rate 3.23769.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 2.053077 | 1.412356 |
| quality_0 | 1.546489 | 0.651496 |
| work_2 | 657.270482 | 0.541168 |
| work_0 | 489.000000 | 0.395458 |
| quality_1 | 1.015609 | 0.300298 |
| position_9 | 1.000000 | 0.202698 |
| age_centered | 0.400000 | -0.182010 |
| work_1 | 517.425865 | 0.173479 |
| prior_debut | 1.000000 | 0.161724 |
| quality_2 | 1.004364 | 0.158208 |
| regular_window_scaled | 1.000000 | -0.132876 |
| draft_college | 1.000000 | 0.118343 |

contact_ridge: reference -0.78206; reconstructed rate 3.55580.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 2.053077 | 1.416596 |
| quality_0 | 1.546489 | 0.654818 |
| work_2 | 657.270482 | 0.544494 |
| work_0 | 489.000000 | 0.405991 |
| quality_1 | 1.015609 | 0.300558 |
| position_9 | 1.000000 | 0.200973 |
| age_centered | 0.400000 | -0.182623 |
| work_1 | 517.425865 | 0.170515 |
| quality_2 | 1.004364 | 0.157930 |
| prior_debut | 1.000000 | 0.157826 |
| regular_window_scaled | 1.000000 | -0.132851 |
| draft_college | 1.000000 | 0.123119 |

contact_hist: reference -0.27038; reconstructed rate 3.16450.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 2.053077 | 2.075036 |
| quality_0 | 1.546489 | 0.680024 |
| MLB_2_pa | 657.000000 | 0.273349 |
| MLB_1_pa | 517.000000 | -0.225115 |
| draft_class_unknown | 0.000000 | 0.171061 |
| position_9 | 1.000000 | 0.162369 |
| pooled_AAA_K | 0.254717 | -0.159133 |
| pooled_MLB_pa | 1296.800000 | 0.106944 |
| shape_AAA_OPPO_OFFB | 0.118462 | 0.088608 |
| pooled_MLB_K | 0.257875 | -0.075617 |
| pooled_MLB_BABIP | 0.342330 | 0.062612 |
| pooled_AAA_HR | 0.026954 | -0.060077 |

Ridge's largest contribution gain raises his rate 3.238 to 3.556 versus 5.379 actual. The origin already contains 45 MLB HR in 489 PA; no MLB shape source exists that year, and only tiny rehab/minor shape enables this refit. Saved coefficient accounting is dominated by MLB quality/work, not a large direct contact effect. This is a useful forecast gain but not proof that minor rehab contact explained his power. The tree lowers his rate slightly and does not share this gain.

Origin-selected peers: Josh Reddick (origin MLB/AAA/AA PA 540/0.0/0.0; expected/actual MLB PA 498.8/487; baseline/ridge/tree rate 0.859/0.914/0.001; actual batting rate -0.200); Justin Bour (origin MLB/AAA/AA PA 429/0.0/9.0; expected/actual MLB PA 468.9/501; baseline/ridge/tree rate 1.264/1.352/0.951; actual batting rate 0.449); Scooter Gennett (origin MLB/AAA/AA PA 497/0.0/0.0; expected/actual MLB PA 500.4/638; baseline/ridge/tree rate 0.780/0.735/0.610; actual batting rate 2.323).

## Yordan Alvarez: 2024 → 2025

Selection: contact_ridge largest value harm; contact_ridge false high.

Age 27.0; stage Current MLB; source position 10; draft pick None; contact-supported application True.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 561 | 106 | 69 | 37 |
| 2023 | AAA | 11 | 1 | 2 | 0 |
| 2023 | MLB | 496 | 92 | 64 | 31 |
| 2024 | MLB | 635 | 95 | 53 | 35 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| MLB | 921.000 | 0.67305 | 0.06934 | 0.35632 |
| AAA | 6.400 | 0.72727 | 0.09398 | 0.30451 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 584.774 | 3.70970 | 5.44249 |
| contact_ridge | 584.774 | 3.94600 | 5.67279 |
| contact_hist | 584.774 | 3.55029 | 5.28713 |
| Actual | 199 | 0.91965 | 0.92510 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00312416). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.97229; reconstructed rate 3.70970.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 2.457089 | 1.888702 |
| work_0 | 635.261424 | 0.764881 |
| quality_0 | 1.415653 | 0.683356 |
| work_2 | 561.000000 | 0.456937 |
| quality_2 | 1.738114 | 0.337737 |
| quality_1 | 1.383087 | 0.321080 |
| position_10 | 1.000000 | 0.295454 |
| reorganized | 1.000000 | -0.276479 |
| pooled_MLB_pa | 2.280667 | -0.246376 |
| prior_debut | 1.000000 | 0.226188 |
| quality_present_1 | 1.000000 | 0.186628 |
| work_1 | 496.000000 | 0.146306 |

contact_ridge: reference -0.94934; reconstructed rate 3.94600.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 2.457089 | 1.862937 |
| work_0 | 635.261424 | 0.709550 |
| quality_0 | 1.415653 | 0.695611 |
| work_2 | 561.000000 | 0.409268 |
| reorganized | 1.000000 | -0.353218 |
| quality_2 | 1.738114 | 0.351220 |
| quality_1 | 1.383087 | 0.342590 |
| position_10 | 1.000000 | 0.290194 |
| prior_debut | 1.000000 | 0.220033 |
| pooled_MLB_pa | 2.280667 | -0.168969 |
| quality_present_1 | 1.000000 | 0.168906 |
| shape_MLB_CENTER_OFFB | 1.594515 | 0.137763 |

contact_hist: reference -0.33086; reconstructed rate 3.55029.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 2.457089 | 2.447860 |
| quality_0 | 1.415653 | 0.530658 |
| pooled_MLB_BB | 0.104604 | 0.187955 |
| pooled_MLB_HR | 0.057886 | 0.141216 |
| shape_MLB_OPPO_GB | 0.041136 | 0.125589 |
| quality_2 | 1.738114 | 0.115775 |
| work_0 | 635.261424 | 0.094756 |
| MLB_2_pa | 561.000000 | 0.091291 |
| position_10 | 1.000000 | 0.077433 |
| shape_MLB_coverage | 0.673049 | -0.072067 |
| shape_MLB_CENTER_LD | 0.108913 | -0.069440 |
| work_2 | 561.000000 | 0.068583 |

Ridge raises an already strong 3.710 rate to 3.946 while actual rate is 0.920 and opportunity 199 versus 585 expected. It therefore worsens this largest contribution harm/false-high case. Strong 635-PA/35-HR/95-K prior production genuinely supports a favorable forecast; the source does not show the later loss of availability. The tree rate is somewhat lower, but neither solves that workload miss. Do not turn the realized bad year into an origin-known warning that was not present.

Origin-selected peers: Gleyber Torres (origin MLB/AAA/AA PA 665/0.0/0.0; expected/actual MLB PA 573.0/628; baseline/ridge/tree rate 0.593/0.677/0.473; actual batting rate 1.063); Willi Castro (origin MLB/AAA/AA PA 635/0.0/0.0; expected/actual MLB PA 518.3/454; baseline/ridge/tree rate -0.383/-0.384/-0.546; actual batting rate -0.523); Bryan De La Cruz (origin MLB/AAA/AA PA 622/0.0/0.0; expected/actual MLB PA 468.2/50; baseline/ridge/tree rate -0.442/-0.338/-0.870; actual batting rate -5.101).

## Aaron Judge: 2021 → 2022

Selection: contact_ridge false low.

Age 29.0; stage Current MLB; source position 9; draft pick 32; contact-supported application True.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2019 | AAA | 19 | 7 | 3 | 1 |
| 2019 | MLB | 447 | 141 | 60 | 27 |
| 2020 | MLB | 114 | 32 | 10 | 9 |
| 2021 | MLB | 633 | 158 | 73 | 39 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| MLB | 393.000 | 0.39601 | 0.04868 | 0.39959 |
| AAA | 5.400 | 0.47368 | 0.09488 | 0.30740 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 482.210 | 2.04558 | 3.15572 |
| contact_ridge | 482.210 | 1.98260 | 3.10511 |
| contact_hist | 482.210 | 2.58878 | 3.59229 |
| Actual | 696 | 6.56063 | 9.78949 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00313500). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.91044; reconstructed rate 2.04558.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 1.561682 | 1.105589 |
| work_0 | 633.260601 | 0.807249 |
| quality_0 | 1.278618 | 0.556754 |
| work_2 | 447.184026 | 0.282999 |
| work_1 | 308.485523 | 0.237970 |
| age_centered | 0.400000 | -0.222969 |
| prior_debut | 1.000000 | 0.171728 |
| pooled_MLB_pa | 1.654000 | -0.166326 |
| quality_2 | 0.843315 | 0.130888 |
| position_9 | 1.000000 | 0.128844 |
| MLB_0_pa | 1.055000 | -0.106305 |
| draft_rank | 0.544036 | 0.093148 |

contact_ridge: reference -0.97826; reconstructed rate 1.98260.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 1.561682 | 1.096852 |
| work_0 | 633.260601 | 0.813866 |
| quality_0 | 1.278618 | 0.556067 |
| work_2 | 447.184026 | 0.287975 |
| work_1 | 308.485523 | 0.247054 |
| age_centered | 0.400000 | -0.224447 |
| prior_debut | 1.000000 | 0.169152 |
| pooled_MLB_pa | 1.654000 | -0.158370 |
| quality_2 | 0.843315 | 0.134966 |
| position_9 | 1.000000 | 0.127395 |
| MLB_0_pa | 1.055000 | -0.101380 |
| draft_rank | 0.544036 | 0.092639 |

contact_hist: reference -0.25633; reconstructed rate 2.58878.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 1.561682 | 2.220245 |
| quality_0 | 1.278618 | 0.352800 |
| pooled_MLB_BB | 0.114427 | 0.178251 |
| pooled_MLB_HR | 0.059868 | 0.157501 |
| pooled_MLB_BABIP | 0.329118 | -0.078833 |
| quality_1 | 0.234741 | -0.071116 |
| MLB_0_pa | 633.000000 | 0.059751 |
| pooled_AAA_BABIP | 0.291985 | -0.037004 |
| MLB_1_pa | 114.000000 | -0.036803 |
| elapsed_scaled | 0.500000 | 0.035539 |
| age_centered | 0.400000 | -0.034440 |
| work_0 | 633.260601 | 0.033996 |

Ridge slightly reduces batting 2.046 to 1.983 before his realized 6.561 season; the tree raises it to 2.589 but still misses greatly. Although modern MLB shape is observed, this cutoff has zero active training players with MLB shape; only earlier minor/rehab shape supports the candidate application. Tree accounting is dominated by pooled MLB quality, not a learned MLB-contact relationship. This limitation prevents calling the new MLB source validated in its very first year.

Origin-selected peers: Nick Castellanos (origin MLB/AAA/AA PA 585/0.0/0.0; expected/actual MLB PA 528.4/558; baseline/ridge/tree rate 1.962/1.962/1.962; actual batting rate -0.190); Trevor Story (origin MLB/AAA/AA PA 595/0.0/0.0; expected/actual MLB PA 564.9/396; baseline/ridge/tree rate 1.422/1.387/1.636; actual batting rate 0.185); Matt Chapman (origin MLB/AAA/AA PA 622/0.0/0.0; expected/actual MLB PA 532.2/621; baseline/ridge/tree rate 0.817/0.817/0.817; actual batting rate 1.068).

## Shea Langeliers: 2022 → 2023

Selection: contact_ridge ordinary.

Age 24.0; stage Current MLB; source position 2; draft pick 9; contact-supported application True.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | AA | 370 | 97 | 33 | 22 |
| 2021 | AAA | 14 | 6 | 3 | 0 |
| 2022 | AAA | 402 | 88 | 43 | 19 |
| 2022 | MLB | 153 | 53 | 9 | 6 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| MLB | 87.000 | 0.56863 | 0.09091 | 0.34225 |
| AAA | 271.000 | 0.65586 | 0.08302 | 0.35849 |
| AA | 186.400 | 0.62973 | 0.09358 | 0.31425 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 176.131 | -0.51619 | 0.39993 |
| contact_ridge | 176.131 | -0.62990 | 0.36655 |
| contact_hist | 176.131 | -0.71647 | 0.34114 |
| Actual | 490 | -1.40990 | 0.36566 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00313097). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.85453; reconstructed rate -0.51619.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| age_centered | -0.600000 | 0.345220 |
| work_0 | 153.000000 | 0.184491 |
| prior_debut | 1.000000 | 0.152714 |
| reorganized | 1.000000 | -0.139112 |
| draft_rank | 0.710926 | 0.128908 |
| position_2 | 1.000000 | -0.124415 |
| draft_class_unknown | 1.000000 | -0.113241 |
| pooled_AA_HR | 0.220202 | 0.088046 |
| pooled_AA_pa | 0.493333 | -0.084443 |
| AA_1_pa | 0.616667 | -0.083806 |
| quality_present_0 | 1.000000 | -0.077926 |
| pooled_AAA_HR | 0.128683 | 0.067397 |

contact_ridge: reference -0.92078; reconstructed rate -0.62990.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| age_centered | -0.600000 | 0.343893 |
| work_0 | 153.000000 | 0.186875 |
| prior_debut | 1.000000 | 0.160422 |
| draft_rank | 0.710926 | 0.124959 |
| shape_MLB_available | 1.000000 | -0.122691 |
| position_2 | 1.000000 | -0.121425 |
| draft_class_unknown | 1.000000 | -0.116527 |
| reorganized | 1.000000 | -0.115568 |
| pooled_AA_HR | 0.220202 | 0.084206 |
| pooled_AA_pa | 0.493333 | -0.080902 |
| AA_1_pa | 0.616667 | -0.077717 |
| quality_present_0 | 1.000000 | -0.073153 |

contact_hist: reference -0.28263; reconstructed rate -0.71647.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_AAA_HR | 0.042868 | 0.251217 |
| pooled_AA_HR | 0.052020 | 0.232872 |
| pooled_AA_2B | 0.038889 | -0.205697 |
| pooled_mlb_quality | -0.079326 | -0.173381 |
| position_2 | 1.000000 | -0.134359 |
| pooled_AA_K | 0.254040 | -0.129940 |
| shape_MLB_CENTER_OFFB | 0.106952 | -0.077269 |
| shape_MLB_OPPO_OFFB | 0.080214 | -0.075153 |
| pooled_MLB_K | 0.300395 | -0.072065 |
| pooled_MLB_HR | 0.035573 | 0.071718 |
| shape_AAA_OPPO_GB | 0.064690 | 0.069131 |
| age_centered | -0.600000 | 0.066493 |

Both new rates become more pessimistic and closer to -1.410 actual, reflecting the 53-K/153-PA MLB debut alongside AAA power. Ridge contribution 0.367 is almost identical to 0.366 realized, but that is cancellation: it expects 176 PA versus 490 actual and overstates batting rate. A near-perfect delivered-value point does not certify smart opportunity or talent. Pratto, Lowe and Kelenic outcomes also show different batting paths despite superficially similar beginnings.

Origin-selected peers: Josh Lowe (origin MLB/AAA/AA PA 198/351.0/0.0; expected/actual MLB PA 188.2/501; baseline/ridge/tree rate 0.055/0.046/-0.704; actual batting rate 1.794); Nick Pratto (origin MLB/AAA/AA PA 182/374.0/0.0; expected/actual MLB PA 266.4/345; baseline/ridge/tree rate 0.387/0.375/0.056; actual batting rate -1.217); Jarred Kelenic (origin MLB/AAA/AA PA 181/394.0/0.0; expected/actual MLB PA 235.7/416; baseline/ridge/tree rate -0.265/-0.336/-0.386; actual batting rate 0.054).

## Alex Bregman: 2017 → 2018

Selection: contact_hist largest value gain.

Age 23.0; stage Current MLB; source position 5; draft pick 2; contact-supported application True.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2015 | A | 133 | 13 | 15 | 1 |
| 2015 | Aplus | 178 | 17 | 12 | 3 |
| 2016 | AA | 285 | 26 | 39 | 14 |
| 2016 | AAA | 83 | 12 | 5 | 6 |
| 2016 | MLB | 217 | 52 | 15 | 8 |
| 2017 | MLB | 626 | 97 | 53 | 19 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| AAA | 52.800 | 0.79518 | 0.10733 | 0.32723 |
| AA | 164.000 | 0.71930 | 0.08333 | 0.31061 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 595.066 | 1.17994 | 3.00076 |
| contact_ridge | 595.066 | 1.29309 | 3.11298 |
| contact_hist | 595.066 | 2.03143 | 3.84525 |
| Actual | 705 | 4.13545 | 7.03058 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00307618). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.63060; reconstructed rate 1.17994.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| work_0 | 626.000000 | 0.801048 |
| age_centered | -0.800000 | 0.383530 |
| pooled_mlb_quality | 0.586276 | 0.374545 |
| quality_0 | 0.544255 | 0.182691 |
| pooled_AA_K | -0.964634 | -0.132471 |
| quality_present_1 | 1.000000 | -0.128473 |
| position_5 | 1.000000 | 0.122078 |
| draft_rank | 0.908807 | 0.101754 |
| draft_class_unknown | 1.000000 | -0.097543 |
| pooled_Aplus_K | -0.694584 | 0.072550 |
| work_1 | 217.178748 | 0.071425 |
| AA_1_pa | 0.475000 | -0.070327 |

contact_ridge: reference -0.63891; reconstructed rate 1.29309.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| work_0 | 626.000000 | 0.813335 |
| age_centered | -0.800000 | 0.385174 |
| pooled_mlb_quality | 0.586276 | 0.374681 |
| quality_0 | 0.544255 | 0.183634 |
| pooled_AA_K | -0.964634 | -0.132819 |
| quality_present_1 | 1.000000 | -0.127127 |
| position_5 | 1.000000 | 0.121436 |
| draft_rank | 0.908807 | 0.102952 |
| draft_class_unknown | 1.000000 | -0.097563 |
| pooled_Aplus_K | -0.694584 | 0.073172 |
| AA_1_pa | 0.475000 | -0.071548 |
| work_1 | 217.178748 | 0.070268 |

contact_hist: reference -0.30123; reconstructed rate 2.03143.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 0.586276 | 0.591567 |
| age_centered | -0.800000 | 0.309461 |
| pooled_Aplus_BABIP | 0.316469 | 0.216799 |
| pooled_AAA_HR | 0.046875 | 0.204213 |
| shape_AA_CENTER_LD | 0.083333 | 0.183830 |
| MLB_0_pa | 626.000000 | 0.145528 |
| shape_AAA_OPPO_OFFB | 0.107330 | 0.128121 |
| draft_rank_low_exposure | 0.056030 | 0.124409 |
| shape_AA_coverage | 0.719298 | 0.086484 |
| pooled_AAA_pa | 66.400000 | 0.073989 |
| shape_AAA_CENTER_LD | 0.075916 | -0.072072 |
| pooled_MLB_2B | 0.060471 | 0.064306 |

The tree's largest contribution gain raises rate 1.180 to 2.031, still below 4.135 realized. There is no MLB shape source that year; older minor shapes, age and pooled MLB quality support the result. Saved paths show both old quality and AA-center-line-drive accounting. This is a real candidate gain, not proof of a causal contact effect, and does not outweigh its systematic losses on other established hitters. Swanson's weaker outcome remains in the origin-selected peer comparison.

Origin-selected peers: Kris Bryant (origin MLB/AAA/AA PA 665/0.0/0.0; expected/actual MLB PA 638.9/457; baseline/ridge/tree rate 3.540/3.540/3.540; actual batting rate 2.129); Manny Machado (origin MLB/AAA/AA PA 690/0.0/0.0; expected/actual MLB PA 631.3/709; baseline/ridge/tree rate 2.143/2.143/2.143; actual batting rate 2.733); Dansby Swanson (origin MLB/AAA/AA PA 551/45.0/0.0; expected/actual MLB PA 368.1/533; baseline/ridge/tree rate -0.798/-0.740/-0.637; actual batting rate -1.538).

## Bo Bichette: 2023 → 2024

Selection: contact_hist false high.

Age 25.0; stage Current MLB; source position 6; draft pick 66; contact-supported application True.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | MLB | 690 | 137 | 40 | 29 |
| 2022 | MLB | 697 | 155 | 41 | 24 |
| 2023 | AAA | 6 | 0 | 0 | 1 |
| 2023 | MLB | 601 | 115 | 27 | 20 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| MLB | 1142.600 | 0.72657 | 0.03863 | 0.47320 |
| AAA | 6.000 | 1.00000 | 0.09434 | 0.31132 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 647.684 | 1.37928 | 3.49417 |
| contact_ridge | 647.684 | 1.34419 | 3.45630 |
| contact_hist | 647.684 | 2.11065 | 4.28367 |
| Actual | 336 | -2.24335 | -0.20699 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00309608). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.95115; reconstructed rate 1.37928.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 1.055496 | 0.815670 |
| work_0 | 601.000000 | 0.766127 |
| work_2 | 690.284068 | 0.580592 |
| pooled_MLB_pa | 2.621000 | -0.301620 |
| position_6 | 1.000000 | -0.294284 |
| quality_0 | 0.546551 | 0.261211 |
| work_1 | 697.000000 | 0.225057 |
| age_centered | -0.400000 | 0.215164 |
| prior_debut | 1.000000 | 0.207816 |
| reorganized | 1.000000 | -0.197988 |
| quality_present_1 | 1.000000 | 0.170638 |
| quality_2 | 0.768237 | 0.143064 |

contact_ridge: reference -0.95564; reconstructed rate 1.34419.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 1.055496 | 0.803275 |
| work_0 | 601.000000 | 0.727640 |
| work_2 | 690.284068 | 0.542402 |
| position_6 | 1.000000 | -0.299920 |
| quality_0 | 0.546551 | 0.264986 |
| reorganized | 1.000000 | -0.228221 |
| age_centered | -0.400000 | 0.218205 |
| pooled_MLB_pa | 2.621000 | -0.209371 |
| prior_debut | 1.000000 | 0.194412 |
| work_1 | 697.000000 | 0.180231 |
| quality_present_1 | 1.000000 | 0.158467 |
| quality_2 | 0.768237 | 0.149349 |

contact_hist: reference -0.31092; reconstructed rate 2.11065.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 1.055496 | 1.494047 |
| age_centered | -0.400000 | 0.549854 |
| position_6 | 1.000000 | -0.132352 |
| quality_2 | 0.768237 | 0.121683 |
| career_mlb_observed_pa | 2328.000000 | 0.106868 |
| shape_MLB_coverage | 0.726567 | -0.106657 |
| pooled_MLB_HBP | 0.004903 | 0.094076 |
| reorganized | 1.000000 | -0.085725 |
| pooled_MLB_HR | 0.035633 | 0.062054 |
| pooled_AAA_HR | 0.037736 | 0.059884 |
| work_0 | 601.000000 | 0.056104 |
| pooled_MLB_BB | 0.054885 | -0.045846 |

The tree amplifies the favorable prior to 2.111 versus the baseline 1.379, but actual batting is -2.243 and PA only 336 versus 648 expected. Pooled quality and age dominate its positive path accounting, not an obvious erroneous event join. Ridge barely lowers the rate. This is a false-high example where recent strong production did not persist, not evidence that the model should have known future injury or collapse. The uncertainty/playing-time layer still needs to represent this downside.

Origin-selected peers: Daulton Varsho (origin MLB/AAA/AA PA 581/0.0/0.0; expected/actual MLB PA 464.6/513; baseline/ridge/tree rate 0.184/0.402/0.290; actual batting rate -0.286); Jeremy Peña (origin MLB/AAA/AA PA 634/0.0/0.0; expected/actual MLB PA 565.0/650; baseline/ridge/tree rate -0.090/0.275/-0.380; actual batting rate -0.253); MJ Melendez (origin MLB/AAA/AA PA 602/0.0/0.0; expected/actual MLB PA 482.8/451; baseline/ridge/tree rate 0.365/0.592/0.234; actual batting rate -0.919).

## Aaron Judge: 2023 → 2024

Selection: contact_hist false low.

Age 31.0; stage Current MLB; source position 9; draft pick 32; contact-supported application True.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | MLB | 633 | 158 | 73 | 39 |
| 2022 | MLB | 696 | 175 | 92 | 62 |
| 2023 | MLB | 458 | 130 | 79 | 37 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| MLB | 788.600 | 0.56547 | 0.07765 | 0.36192 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 552.952 | 3.39964 | 4.84504 |
| contact_ridge | 552.952 | 3.52146 | 4.95731 |
| contact_hist | 552.952 | 2.99801 | 4.47491 |
| Actual | 704 | 7.55765 | 11.06615 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00309608). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.90645; reconstructed rate 3.39964.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 2.791562 | 2.064682 |
| quality_0 | 1.317130 | 0.579770 |
| work_0 | 458.000000 | 0.557029 |
| quality_1 | 2.408333 | 0.523708 |
| age_centered | 0.800000 | -0.457044 |
| work_2 | 633.260601 | 0.409208 |
| work_1 | 696.000000 | 0.332152 |
| quality_2 | 1.278618 | 0.228532 |
| reorganized | 1.000000 | -0.206516 |
| pooled_MLB_pa | 2.324333 | -0.176324 |
| prior_debut | 1.000000 | 0.175350 |
| pooled_MLB_BB | 0.567590 | 0.153237 |

contact_ridge: reference -0.92008; reconstructed rate 3.52146.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 2.791562 | 2.033243 |
| quality_0 | 1.317130 | 0.575328 |
| quality_1 | 2.408333 | 0.540802 |
| work_0 | 458.000000 | 0.539868 |
| age_centered | 0.800000 | -0.461601 |
| work_2 | 633.260601 | 0.385627 |
| work_1 | 696.000000 | 0.310716 |
| quality_2 | 1.278618 | 0.242972 |
| reorganized | 1.000000 | -0.227397 |
| prior_debut | 1.000000 | 0.167164 |
| pooled_MLB_BB | 0.567590 | 0.149217 |
| position_9 | 1.000000 | 0.136230 |

contact_hist: reference -0.30596; reconstructed rate 2.99801.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | 2.791562 | 2.291604 |
| quality_0 | 1.317130 | 0.375805 |
| pooled_MLB_BB | 0.136759 | 0.216992 |
| quality_2 | 1.278618 | 0.202933 |
| age_centered | 0.800000 | -0.183575 |
| pooled_MLB_BABIP | 0.322761 | -0.169927 |
| pooled_MLB_HR | 0.075606 | 0.135175 |
| pooled_MLB_pa | 1394.600000 | 0.116146 |
| work_1 | 696.000000 | 0.088318 |
| pooled_MLB_3B | 0.000335 | -0.081758 |
| quality_1 | 2.408333 | 0.064538 |
| pooled_MLB_K | 0.259467 | 0.054094 |

Ridge improves the rate modestly (3.400 to 3.521), while the tree reduces it to 2.998 versus the extraordinary 7.558 realized. His 37 HR in 458 PA and longer elite production remain visible. The tree's flattening of exceptional hitters is a repeatable architectural weakness in these cases; adding shape does not fix it. PA is also low (553 versus 704). No hand-coded Judge-only increase or retrospective recalibration is justified.

Origin-selected peers: Randal Grichuk (origin MLB/AAA/AA PA 471/36.0/0.0; expected/actual MLB PA 346.3/279; baseline/ridge/tree rate -0.342/-0.348/-0.874; actual batting rate 3.176); Taylor Ward (origin MLB/AAA/AA PA 409/0.0/0.0; expected/actual MLB PA 477.5/663; baseline/ridge/tree rate 0.860/1.093/0.567; actual batting rate 0.840); Connor Joe (origin MLB/AAA/AA PA 472/0.0/0.0; expected/actual MLB PA 436.0/416; baseline/ridge/tree rate 0.393/0.440/0.130; actual batting rate -0.183).

## Emmanuel Rivera: 2023 → 2024

Selection: contact_hist ordinary.

Age 27.0; stage Current MLB; source position 5; draft pick 579; contact-supported application True.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | AA | 18 | 4 | 2 | 0 |
| 2021 | AAA | 282 | 58 | 22 | 19 |
| 2021 | MLB | 98 | 21 | 8 | 1 |
| 2022 | AAA | 85 | 16 | 10 | 3 |
| 2022 | MLB | 359 | 83 | 23 | 12 |
| 2023 | AAA | 129 | 18 | 12 | 5 |
| 2023 | MLB | 283 | 56 | 22 | 4 |

| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |
|---|---:|---:|---:|---:|
| MLB | 437.000 | 0.69475 | 0.03762 | 0.44134 |
| AAA | 263.000 | 0.71819 | 0.04738 | 0.40220 |
| AA | 7.200 | 0.66667 | 0.10448 | 0.31343 |

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 227.215 | -0.50644 | 0.51169 |
| contact_ridge | 227.215 | -0.42601 | 0.54215 |
| contact_hist | 227.215 | -0.50811 | 0.51106 |
| Actual | 302 | -0.86079 | 0.50985 |

Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement 0.00309608). This is not full WAR or a joint predictive distribution.

Benchmark ridge: reference -0.78542; reconstructed rate -0.50644.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| work_0 | 283.000000 | 0.364907 |
| reorganized | 1.000000 | -0.195725 |
| pooled_mlb_quality | -0.218825 | -0.167122 |
| quality_present_1 | 1.000000 | 0.126304 |
| prior_debut | 1.000000 | 0.096121 |
| position_5 | 1.000000 | 0.093351 |
| quality_0 | -0.201286 | -0.086373 |
| pooled_AAA_HR | 0.167610 | 0.085912 |
| pooled_MLB_pa | 1.048333 | -0.083912 |
| work_2 | 98.040346 | 0.072128 |
| draft_class_unknown | 1.000000 | -0.064299 |
| on_40man | 1.000000 | 0.063126 |

contact_ridge: reference -0.76869; reconstructed rate -0.42601.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| work_0 | 283.000000 | 0.339461 |
| reorganized | 1.000000 | -0.253436 |
| pooled_mlb_quality | -0.218825 | -0.163658 |
| quality_present_1 | 1.000000 | 0.115663 |
| position_5 | 1.000000 | 0.095251 |
| shape_AAA_PULL_GB | 1.928375 | -0.092844 |
| quality_0 | -0.201286 | -0.087687 |
| pooled_AAA_HR | 0.167610 | 0.082412 |
| prior_debut | 1.000000 | 0.080932 |
| shape_AA_available | 1.000000 | -0.070978 |
| draft_class_unknown | 1.000000 | -0.067790 |
| quality_present_0 | 1.000000 | -0.066200 |

contact_hist: reference -0.25159; reconstructed rate -0.50811.

| Feature | Model input | Rate accounting |
|---|---:|---:|
| pooled_mlb_quality | -0.218825 | -0.398403 |
| shape_MLB_PULL_LD | 0.083799 | -0.135266 |
| pooled_AAA_HR | 0.046761 | 0.133065 |
| shape_MLB_OPPO_OFFB | 0.099069 | 0.114930 |
| shape_MLB_CENTER_LD | 0.110242 | -0.088411 |
| quality_0 | -0.201286 | -0.084022 |
| pooled_AAA_BB | 0.088374 | 0.083946 |
| position_2 | 0.000000 | 0.067679 |
| pooled_AAA_2B | 0.060489 | 0.058468 |
| shape_MLB_coverage | 0.694754 | -0.045203 |
| shape_MLB_PULL_OFFB | 0.037616 | 0.040244 |
| shape_MLB_CENTER_GB | 0.161266 | 0.038893 |

The tree is almost unchanged at -0.508; ridge rises to -0.426, farther from -0.861 actual. The tree's delivered value 0.511 closely matches 0.510 actual because its 227 expected PA versus 302 actual offsets an overly favorable rate. Saved paths include MLB line-drive/fly shapes and pooled quality, but this is another cancellation, not strong component accuracy. Julks/Short/Trejo provide unsuccessful origin-selected peers rather than only highlighting survivors.

Origin-selected peers: Corey Julks (origin MLB/AAA/AA PA 323/129.0/0.0; expected/actual MLB PA 224.0/189; baseline/ridge/tree rate -0.769/-0.855/-1.030; actual batting rate -2.398); Zack Short (origin MLB/AAA/AA PA 253/100.0/0.0; expected/actual MLB PA 163.7/88; baseline/ridge/tree rate -1.176/-1.039/-1.340; actual batting rate -4.275); Alan Trejo (origin MLB/AAA/AA PA 227/54.0/0.0; expected/actual MLB PA 164.6/67; baseline/ridge/tree rate -1.156/-0.986/-0.814; actual batting rate -7.845).

## Disposition

Do not adopt either contact-rate candidate. Ridge loses slightly and uncertainly; the histogram candidate loses materially overall and compresses exceptional established hitters. Small player gains do not repair first-arrival/return opportunity or fast-entry talent. Preserve the raw reconstructed input and its source flags as reusable infrastructure; do not conclude all shape, shape×outcome or park-adjusted talent models are useless. Close this bounded transfer batch rather than search parameter/prior variants until one wins.
