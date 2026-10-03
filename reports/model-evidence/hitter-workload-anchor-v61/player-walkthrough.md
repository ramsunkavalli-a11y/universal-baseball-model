# Direct and anchored playing time actual player reviews

Both global replacements are withheld after review. Corrected V53 remains the research baseline.
The anchored arm keeps observed prior workload outside the trees and learns its adjustment; that reference is not a promised job.
All 30,506 rows remain. Seventy heads replay. Hitting talent and availability overrides are unchanged.
New models predict expected PA only; no appearance probability is invented from a direct mean.
Peer selection uses origin-known stage/debut, age, recent MLB/minor PA and reference workload, not future success.
Tree-path terms account for each fitted output, not causal effects or an additive decomposition of the refit change.

## Aaron Judge at the 2022 cutoff

Selection: fixed diagnostic.
Age 30.0; stage Current MLB; current/prior MLB PA 696/633/114; captured listing 0.
Reference 696.000000 PA; actual workload-profile support 77 distinct training people.
Preserved baseline appearance 0.9587 × conditional PA 529.154 = 507.294 expected PA.
Direct 477.070; anchored 459.798; next-year actual 458 PA.
Fixed hitting estimate 3.259 versus observable realized 5.312 per 600 PA.
Batting plus replacement: baseline 4.344, direct 4.085, anchored 3.937, actual 5.489.

696/633/114 actual MLB PA and 62/39/9 HR are retained. The short 2020 workload becomes a 308.49 reference, not added talent observations; his maximum reference is 696. The anchored head learns -236.20, leaving 459.80 PA versus 458 actual. Direct gives 477.07 and baseline 507.29. This improves workload but worsens offense because fixed hitting talent 3.259 is below realized 5.312. The anchored path includes a -53.17 captured non-listing effect, despite his known December re-signing in the broader source. The reference is not proof that roster/job context is fixed. Successful Ramirez/Turner/Suarez and Frazier's 455 PA stay visible.

Known source counts:
- 2020 MLB: 114 PA, 9 HR, 32 K, 10 unintentional walks.
- 2021 MLB: 633 PA, 39 HR, 158 K, 73 unintentional walks.
- 2022 MLB: 696 PA, 62 HR, 175 K, 92 unintentional walks.

Workload reference arithmetic:
- 2022: 696 actual PA × 162 / 162.000000 league-average completed games = 696.000000, subject to the declared 800 upper bound.
- 2021: 633 actual PA × 162 / 161.933333 league-average completed games = 633.260601, subject to the declared 800 upper bound.
- 2020: 114 actual PA × 162 / 59.866667 league-average completed games = 308.485523, subject to the declared 800 upper bound.
- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.

Reconstructed pooled count inputs:
- MLB: weighted PA 1270.800, K 320.600, HR 98.600; fixed-100 K 0.250657, HR 0.074117. Actual model inputs verified.
- AAA: weighted PA 0.000, K 0.000, HR 0.000; fixed-100 K 0.230000, HR 0.030000. Actual model inputs verified.

Corrected availability inputs:
- op_medical_scope: 1.000000; exposed training people 997.
- op_recorded_unresolved: 0.000000; exposed training people 14.
- op_log_possible_days_upper: 2.564949; exposed training people 609.
- op_observed_returns: 0.000000; exposed training people 31.
- op_roster_returns: 0.000000; exposed training people 146.
- op_nonmedical_unresolved: 0.000000; exposed training people 28.

Saved direct61 head: node reference 38.592628; output 477.069673 (next_pa).
After addback, raw PA 477.069673; after bounds/policy 477.069673. Training people 10779.
Largest fitted path terms:
- work_0: input 696.000000, path term +304.795540 PA.
- quality_0: input 2.408333, path term +73.241121 PA.
- role_mlb_0: input 4.407186, path term +48.030737 PA.
- workload_reference: input 696.000000, path term +40.583376 PA.
- on_40man: input 0.000000, path term -39.777655 PA.
- pooled_MLB_K: input 0.250657, path term -26.847580 PA.
- pooled_mlb_quality: input 2.681818, path term +13.691144 PA.
- age_centered: input 0.600000, path term +11.749384 PA.
Availability path terms: op_log_possible_days_upper +2.740472.

Saved anchor61 head: node reference -100.455897; output -236.201828 (adjustment_target).
After addback, raw PA 459.798172; after bounds/policy 459.798172. Training people 10779.
Largest fitted path terms:
- workload_reference: input 696.000000, path term -100.449021 PA.
- quality_0: input 2.408333, path term +54.362171 PA.
- on_40man: input 0.000000, path term -53.165285 PA.
- games_mlb_2: input 75.600000, path term -47.211436 PA.
- work_0: input 696.000000, path term +21.893191 PA.
- pooled_MLB_K: input 0.250657, path term -13.317065 PA.
- games_mlb_1: input 148.000000, path term -9.305359 PA.
- pooled_MLB_3B: input 0.000365, path term -8.017547 PA.
Availability path terms: op_log_possible_days_upper +2.328736.

Cutoff-known relevant records:
- Known 2021-07-16, occurred 2021-07-16: New York Yankees placed RF Aaron Judge on the 10-day injured list..
- Known 2021-07-27, occurred 2021-07-27: New York Yankees activated RF Aaron Judge from the 10-day injured list..
- Known 2021-07-27, occurred 2021-07-27: New York Yankees activated RF Aaron Judge from the 10-day injured list..
- Known 2022-12-20, occurred 2022-12-20: New York Yankees signed free agent RF Aaron Judge..

Origin-known comparisons, all retained:
- José Ramírez: age 29.0, current/prior MLB PA 685/636, reference 687.33; baseline/direct/anchored 585.78/608.89/621.36, actual 691 PA, 3.835 offense value.
- Trea Turner: age 29.0, current/prior MLB PA 708/646, reference 708.00; baseline/direct/anchored 635.53/633.69/628.88, actual 691 PA, 3.682 offense value.
- Adam Frazier: age 30.0, current/prior MLB PA 602/639, reference 639.26; baseline/direct/anchored 446.97/444.18/459.28, actual 455 PA, 1.171 offense value.
- Eugenio Suárez: age 30.0, current/prior MLB PA 629/574, reference 629.00; baseline/direct/anchored 506.62/534.95/484.31, actual 694 PA, 2.610 offense value.

## Aaron Judge at the 2016 cutoff

Selection: fixed diagnostic, direct61: largest delivered harm, direct61: false low, anchor61: false low.
Age 24.0; stage Current MLB; current/prior MLB PA 95/0/0; captured listing 1.
Reference 100.000000 PA; actual workload-profile support 208 distinct training people.
Preserved baseline appearance 0.9259 × conditional PA 304.039 = 281.499 expected PA.
Direct 180.765; anchored 209.351; next-year actual 678 PA.
Fixed hitting estimate -0.040 versus observable realized 5.557 per 600 PA.
Batting plus replacement: baseline 0.851, direct 0.546, anchored 0.633, actual 8.374.

AAA 410 PA/19 HR/98 K versus MLB 95/4/42 remain in the actual inputs. The workload reference floors at 100, not a guaranteed MLB role. Direct falls from baseline 281.50 to 180.77 PA and anchored gives 209.35 versus 678. Both miss the breakout and the unchanged near-neutral hitting grade. Scout signal and AAA use add opportunity on each actual path; early medical inputs are unsupported and have no path terms. Origin-matched Moya/Austin/Difo/Toles include zero and limited opportunities. No blanket 678-PA assignment is justified, but neither challenger repairs brief-debut readiness.

Known source counts:
- 2014 A: 278 PA, 9 HR, 59 K, 38 unintentional walks.
- 2014 Aplus: 285 PA, 8 HR, 72 K, 49 unintentional walks.
- 2015 AA: 280 PA, 12 HR, 70 K, 23 unintentional walks.
- 2015 AAA: 260 PA, 8 HR, 74 K, 29 unintentional walks.
- 2016 AAA: 410 PA, 19 HR, 98 K, 47 unintentional walks.
- 2016 MLB: 95 PA, 4 HR, 42 K, 9 unintentional walks.

Workload reference arithmetic:
- 2016: 95 actual PA × 162 / 161.866667 league-average completed games = 95.078254, subject to the declared 800 upper bound.
- 2015: 0 actual PA × 162 / 161.933333 league-average completed games = 0.000000, subject to the declared 800 upper bound.
- 2014: 0 actual PA × 162 / 162.000000 league-average completed games = 0.000000, subject to the declared 800 upper bound.
- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.

Reconstructed pooled count inputs:
- MLB: weighted PA 95.000, K 42.000, HR 4.000; fixed-100 K 0.333333, HR 0.035897. Actual model inputs verified.
- AAA: weighted PA 618.000, K 157.200, HR 25.400; fixed-100 K 0.250975, HR 0.039554. Actual model inputs verified.

Corrected availability inputs:
- op_medical_scope: 1.000000; exposed training people 0.
- op_recorded_unresolved: 0.000000; exposed training people 0.
- op_log_possible_days_upper: 2.995732; exposed training people 0.
- op_observed_returns: 0.000000; exposed training people 0.
- op_roster_returns: 0.000000; exposed training people 0.
- op_nonmedical_unresolved: 0.000000; exposed training people 4.

Saved direct61 head: node reference 38.360613; output 180.765231 (next_pa).
After addback, raw PA 180.765231; after bounds/policy 180.765231. Training people 6604.
Largest fitted path terms:
- on_40man: input 1.000000, path term +75.423778 PA.
- scout_rank_score_0: input 0.700000, path term +53.971869 PA.
- role_pool_AAA: input 4.334651, path term +27.525534 PA.
- MLB_0_pa: input 95.000000, path term +20.822176 PA.
- pooled_AA_K: input 0.243827, path term -13.809556 PA.
- age_centered: input -0.600000, path term +11.102796 PA.
- pooled_MLB_K: input 0.333333, path term -9.745520 PA.
- quality_0: input -0.175091, path term -9.007512 PA.
Availability path terms: none.

Saved anchor61 head: node reference -100.359715; output 109.351420 (adjustment_target).
After addback, raw PA 209.351420; after bounds/policy 209.351420. Training people 6604.
Largest fitted path terms:
- scout_rank_score_0: input 0.700000, path term +77.513251 PA.
- on_40man: input 1.000000, path term +39.324597 PA.
- role_pool_AAA: input 4.334651, path term +19.381781 PA.
- AAA_0_pa: input 410.000000, path term +17.869743 PA.
- MLB_0_pa: input 95.000000, path term +17.028569 PA.
- pooled_AA_K: input 0.243827, path term -11.248251 PA.
- pooled_MLB_K: input 0.333333, path term -10.374128 PA.
- role_pool_AA: input 4.370861, path term +9.364406 PA.
Availability path terms: none.

Cutoff-known relevant records:
- Known 2016-08-13, occurred 2016-08-13: New York Yankees selected the contract of RF Aaron Judge from Scranton/Wilkes-Barre RailRiders..
- Known 2016-09-14, occurred 2016-09-14: New York Yankees placed RF Aaron Judge on the 15-day disabled list. Right oblique strain..
- Known 2016-10-03, occurred 2016-10-03: New York Yankees activated RF Aaron Judge from the 15-day disabled list..

Origin-known comparisons, all retained:
- Steven Moya: age 24.0, current/prior MLB PA 100/25, reference 100.08; baseline/direct/anchored 231.20/205.89/189.33, actual 0 PA, 0.000 offense value.
- Tyler Austin: age 24.0, current/prior MLB PA 90/0, reference 100.00; baseline/direct/anchored 91.79/140.50/123.80, actual 46 PA, 0.074 offense value.
- Wilmer Difo: age 24.0, current/prior MLB PA 66/11, reference 100.00; baseline/direct/anchored 202.04/203.27/190.26, actual 365 PA, 0.253 offense value.
- Andrew Toles: age 24.0, current/prior MLB PA 115/0, reference 115.09; baseline/direct/anchored 222.84/237.44/180.52, actual 102 PA, 0.453 offense value.

## Fernando Tatis Jr. at the 2022 cutoff

Selection: fixed diagnostic, anchor61: largest delivered gain.
Age 23.0; stage Upper minors; current/prior MLB PA 0/546/257; captured listing 0.
Reference 695.445434 PA; actual workload-profile support 0 distinct training people.
Preserved baseline appearance 0.1260 × conditional PA 275.953 = 34.768 expected PA.
Direct 161.052; anchored 321.858; next-year actual 635 PA.
Fixed hitting estimate 1.289 versus observable realized 1.271 per 600 PA.
Batting plus replacement: baseline 0.184, direct 0.850, anchored 1.699, actual 3.333.

546 PA/42 HR in 2021, 257/17 in short 2020 and the 14-PA AA rehabilitation stint survive. Annualizing 2020 gives a 695.45 workload reference, not proof he previously had a 695-PA full season. Learned adjustment -373.59 leaves 321.86 versus baseline 34.77, direct 161.05 and actual 635. Fixed hitting talent 1.289 is close to realized 1.271, so this is a real opportunity/value improvement, not canceled errors. The finite 80-game suspension is captured only as an unresolved nonmedical signal; it is not a permanent zero or a model of remaining suspended games. Exact workload-profile support is zero; White/Bauers/Peters/Long are not equally talented suspension cases. Improvement does not validate the rare legal-return mechanism.

Known source counts:
- 2020 MLB: 257 PA, 17 HR, 61 K, 26 unintentional walks.
- 2021 MLB: 546 PA, 42 HR, 153 K, 56 unintentional walks.
- 2022 AA: 14 PA, 0 HR, 2 K, 4 unintentional walks.

Workload reference arithmetic:
- 2022: 0 actual PA × 162 / 162.000000 league-average completed games = 0.000000, subject to the declared 800 upper bound.
- 2021: 546 actual PA × 162 / 161.933333 league-average completed games = 546.224784, subject to the declared 800 upper bound.
- 2020: 257 actual PA × 162 / 59.866667 league-average completed games = 695.445434, subject to the declared 800 upper bound.
- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.

Reconstructed pooled count inputs:
- MLB: weighted PA 591.000, K 159.000, HR 43.800; fixed-100 K 0.263386, HR 0.067728. Actual model inputs verified.
- AAA: weighted PA 0.000, K 0.000, HR 0.000; fixed-100 K 0.230000, HR 0.030000. Actual model inputs verified.

Corrected availability inputs:
- op_medical_scope: 1.000000; exposed training people 1011.
- op_recorded_unresolved: 0.000000; exposed training people 17.
- op_log_possible_days_upper: 5.087596; exposed training people 596.
- op_observed_returns: 0.000000; exposed training people 25.
- op_roster_returns: 0.000000; exposed training people 147.
- op_nonmedical_unresolved: 1.000000; exposed training people 34.

Saved direct61 head: node reference 38.197886; output 161.052130 (next_pa).
After addback, raw PA 161.052130; after bounds/policy 161.052130. Training people 10867.
Largest fitted path terms:
- workload_reference: input 695.445434, path term +57.591871 PA.
- pooled_mlb_quality: input 1.367368, path term +31.269504 PA.
- age_centered: input -0.800000, path term +24.654372 PA.
- on_40man: input 0.000000, path term -19.738806 PA.
- games_mlb_2: input 159.300000, path term +19.733867 PA.
- work_0: input 0.000000, path term -19.673623 PA.
- pooled_MLB_K: input 0.263386, path term -12.046782 PA.
- role_pool_MLB: input 4.223561, path term +9.044777 PA.
Availability path terms: op_log_possible_days_upper +4.435135; op_nonmedical_unresolved -3.216857.

Saved anchor61 head: node reference -100.268404; output -373.587770 (adjustment_target).
After addback, raw PA 321.857664; after bounds/policy 321.857664. Training people 10867.
Largest fitted path terms:
- workload_reference: input 695.445434, path term -91.925861 PA.
- on_40man: input 0.000000, path term -72.540674 PA.
- games_mlb_2: input 159.300000, path term -63.126179 PA.
- work_0: input 0.000000, path term -60.044967 PA.
- pooled_mlb_quality: input 1.367368, path term +39.921757 PA.
- quality_1: input 1.347879, path term +17.060441 PA.
- games_mlb_0: input 0.000000, path term -16.571939 PA.
- MLB_2_pa: input 257.000000, path term +14.579917 PA.
Availability path terms: op_nonmedical_unresolved -6.322623; op_log_possible_days_upper +3.418700.

Cutoff-known relevant records:
- Known 2021-04-06, occurred 2021-04-06: San Diego Padres placed SS Fernando Tatis Jr. on the 10 day injured list. Left shoulder inflammation..
- Known 2021-04-16, occurred 2021-04-16: San Diego Padres activated SS Fernando Tatis Jr. from the 10-day injured list..
- Known 2021-05-11, occurred 2021-05-11: San Diego Padres placed SS Fernando Tatis Jr. on the 10-day injured list..
- Known 2021-05-19, occurred 2021-05-19: San Diego Padres activated SS Fernando Tatis Jr. from the 10-day injured list..
- Known 2021-07-31, occurred 2021-07-31: San Diego Padres placed SS Fernando Tatis Jr. on the 10-day injured list. Left shoulder inflammation..
- Known 2021-08-15, occurred 2021-08-15: San Diego Padres activated SS Fernando Tatis Jr. from the 10-day injured list..
- Known 2022-04-07, occurred 2022-04-07: San Diego Padres placed SS Fernando Tatis Jr. on the 60-day injured list. Left wrist fracture..
- Known 2022-08-12, occurred 2022-08-12: sourced game-count suspension.

Origin-known comparisons, all retained:
- Evan White: age 26.0, current/prior MLB PA 0/104, reference 546.61; baseline/direct/anchored 75.17/162.25/219.08, actual 0 PA, 0.000 offense value.
- Jake Bauers: age 26.0, current/prior MLB PA 0/315, reference 315.13; baseline/direct/anchored 7.32/8.36/35.70, actual 272 PA, 0.662 offense value.
- DJ Peters: age 26.0, current/prior MLB PA 0/240, reference 240.10; baseline/direct/anchored 6.16/19.04/29.61, actual 0 PA, 0.000 offense value.
- Shed Long Jr.: age 26.0, current/prior MLB PA 0/121, reference 346.37; baseline/direct/anchored 7.50/48.00/42.81, actual 0 PA, 0.000 offense value.

## Matt McLain at the 2024 cutoff

Selection: fixed diagnostic.
Age 24.0; stage Inactive / unknown; current/prior MLB PA 0/403/0; captured listing 0.
Reference 403.000000 PA; actual workload-profile support 2 distinct training people.
Preserved baseline appearance 0.5360 × conditional PA 323.937 = 173.619 expected PA.
Direct 154.385; anchored 233.213; next-year actual 577 PA.
Fixed hitting estimate 0.251 versus observable realized -1.140 per 600 PA.
Batting plus replacement: baseline 0.615, direct 0.547, anchored 0.826, actual 0.707.

Known shoulder surgery/October plain activation and previous MLB 403 PA/16 HR, AAA 180/12, AA 452/17 remain. Reference 403 plus adjustment -169.79 yields 233.21 versus baseline 173.62, direct 154.39 and actual 577. Only two people match this broad origin-known workload profile. The plain-return input has no anchored path split; the gain must not be called a learned surgical recovery. Fixed hitting 0.251 exceeds realized -1.140, so baseline offense 0.615 was already close to 0.707 partly through error cancellation. Raising PA improves workload but anchored offense 0.826 is farther away. Mauricio's 184 PA and non-arriving comparisons remain included.

Known source counts:
- 2022 AA: 452 PA, 17 HR, 127 K, 69 unintentional walks.
- 2023 AAA: 180 PA, 12 HR, 37 K, 29 unintentional walks.
- 2023 MLB: 403 PA, 16 HR, 115 K, 31 unintentional walks.

Workload reference arithmetic:
- 2024: 0 actual PA × 162 / 161.933333 league-average completed games = 0.000000, subject to the declared 800 upper bound.
- 2023: 403 actual PA × 162 / 162.000000 league-average completed games = 403.000000, subject to the declared 800 upper bound.
- 2022: 0 actual PA × 162 / 162.000000 league-average completed games = 0.000000, subject to the declared 800 upper bound.
- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.

Reconstructed pooled count inputs:
- MLB: weighted PA 322.400, K 92.000, HR 12.800; fixed-100 K 0.272254, HR 0.037405. Actual model inputs verified.
- AAA: weighted PA 144.000, K 29.600, HR 9.600; fixed-100 K 0.215574, HR 0.051639. Actual model inputs verified.

Corrected availability inputs:
- op_medical_scope: 1.000000; exposed training people 1191.
- op_recorded_unresolved: 0.000000; exposed training people 21.
- op_log_possible_days_upper: 5.389072; exposed training people 685.
- op_observed_returns: 0.000000; exposed training people 33.
- op_roster_returns: 1.000000; exposed training people 192.
- op_nonmedical_unresolved: 0.000000; exposed training people 31.

Saved direct61 head: node reference 39.296520; output 154.385053 (next_pa).
After addback, raw PA 154.385053; after bounds/policy 154.385053. Training people 11978.
Largest fitted path terms:
- role_pool_AAA: input 4.380952, path term +37.114493 PA.
- pooled_mlb_quality: input 0.566746, path term +22.698444 PA.
- work_0: input 0.000000, path term -22.339945 PA.
- age_centered: input -0.600000, path term +20.981021 PA.
- pooled_AAA_HR: input 0.051639, path term +17.237769 PA.
- draft_rank: input 0.627253, path term +11.670777 PA.
- games_mlb_0: input 0.000000, path term +7.881884 PA.
- op_log_possible_days_upper: input 5.389072, path term +7.620766 PA.
Availability path terms: op_log_possible_days_upper +7.620766; op_nonmedical_unresolved +0.006638; op_observed_returns +0.005728; op_roster_returns +0.005181.

Saved anchor61 head: node reference -100.821962; output -169.787112 (adjustment_target).
After addback, raw PA 233.212888; after bounds/policy 233.212888. Training people 11978.
Largest fitted path terms:
- workload_reference: input 403.000000, path term -74.206683 PA.
- work_0: input 0.000000, path term -27.147351 PA.
- pooled_AAA_HR: input 0.051639, path term +25.312322 PA.
- age_centered: input -0.600000, path term +22.386530 PA.
- role_pool_AAA: input 4.380952, path term +18.755847 PA.
- work_1: input 403.000000, path term -15.995762 PA.
- on_40man: input 0.000000, path term -12.739968 PA.
- draft_rank: input 0.627253, path term +10.832117 PA.
Availability path terms: op_log_possible_days_upper +2.474309; op_nonmedical_unresolved +0.006718; op_observed_returns +0.003173.

Cutoff-known relevant records:
- Known 2023-05-15, occurred 2023-05-15: Cincinnati Reds selected the contract of SS Matt McLain from Louisville Bats..
- Known 2023-08-28, occurred 2023-08-28: Cincinnati Reds placed SS Matt McLain on the 10-day injured list. Right oblique strain..
- Known 2023-10-02, occurred 2023-10-02: Cincinnati Reds activated SS Matt McLain from the 10-day injured list..
- Known 2024-03-27, occurred 2024-03-27: Cincinnati Reds placed SS Matt McLain on the 10-day injured list. Left shoulder surgery..
- Known 2024-03-28, occurred 2024-03-28: Cincinnati Reds transferred SS Matt McLain from the 10-day injured list to the 60-day injured list. Left shoulder surgery..
- Known 2024-10-28, occurred 2024-10-28: Cincinnati Reds activated SS Matt McLain..

Origin-known comparisons, all retained:
- Wander Franco: age 23.0, current/prior MLB PA 0/491, reference 491.00; baseline/direct/anchored 83.54/118.31/154.34, actual 0 PA, 0.000 offense value.
- Tucupita Marcano: age 24.0, current/prior MLB PA 0/220, reference 220.00; baseline/direct/anchored 0.00/0.00/0.00, actual 0 PA, 0.000 offense value.
- Ronny Mauricio: age 23.0, current/prior MLB PA 0/108, reference 108.00; baseline/direct/anchored 113.84/139.77/140.24, actual 184 PA, 0.273 offense value.
- Sherten Apostel: age 25.0, current/prior MLB PA 0/0, reference 100.00; baseline/direct/anchored 0.67/2.65/0.00, actual 0 PA, 0.000 offense value.

## Gavin Lux at the 2023 cutoff

Selection: fixed diagnostic.
Age 25.0; stage Inactive / unknown; current/prior MLB PA 0/471/381; captured listing 1.
Reference 471.000000 PA; actual workload-profile support 12 distinct training people.
Preserved baseline appearance 0.7809 × conditional PA 277.395 = 216.623 expected PA.
Direct 233.678; anchored 197.095; next-year actual 487 PA.
Fixed hitting estimate -0.243 versus observable realized -0.388 per 600 PA.
Batting plus replacement: baseline 0.583, direct 0.629, anchored 0.530, actual 1.193.

Prior 471 and 381 MLB PA, knee surgery and November named IL activation are preserved. Reference 471 plus -273.90 gives 197.10 versus baseline 216.62, direct 233.68 and actual 487. The reference construction helps the absence group overall but makes this surgical comeback worse. Both negative current-zero and older-game path terms survive; positive roster and possible-absence terms do not solve readiness. Twelve matching profile people and ordinary failed inactive peers are not equivalent surgical return support. Do not claim the entire medical-comeback problem solved from the group RMSE.

Known source counts:
- 2021 AAA: 74 PA, 1 HR, 15 K, 6 unintentional walks.
- 2021 MLB: 381 PA, 7 HR, 83 K, 38 unintentional walks.
- 2022 MLB: 471 PA, 6 HR, 95 K, 47 unintentional walks.

Workload reference arithmetic:
- 2023: 0 actual PA × 162 / 162.000000 league-average completed games = 0.000000, subject to the declared 800 upper bound.
- 2022: 471 actual PA × 162 / 162.000000 league-average completed games = 471.000000, subject to the declared 800 upper bound.
- 2021: 381 actual PA × 162 / 161.933333 league-average completed games = 381.156855, subject to the declared 800 upper bound.
- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.

Reconstructed pooled count inputs:
- MLB: weighted PA 605.400, K 125.800, HR 9.000; fixed-100 K 0.210944, HR 0.017012. Actual model inputs verified.
- AAA: weighted PA 44.400, K 9.000, HR 0.600; fixed-100 K 0.221607, HR 0.024931. Actual model inputs verified.

Corrected availability inputs:
- op_medical_scope: 1.000000; exposed training people 1121.
- op_recorded_unresolved: 0.000000; exposed training people 16.
- op_log_possible_days_upper: 5.209486; exposed training people 662.
- op_observed_returns: 0.000000; exposed training people 33.
- op_roster_returns: 0.000000; exposed training people 193.
- op_nonmedical_unresolved: 0.000000; exposed training people 31.

Saved direct61 head: node reference 38.986315; output 233.677921 (next_pa).
After addback, raw PA 233.677921; after bounds/policy 233.677921. Training people 11424.
Largest fitted path terms:
- on_40man: input 1.000000, path term +90.248165 PA.
- work_0: input 0.000000, path term -35.626697 PA.
- pooled_mlb_quality: input 0.150719, path term +30.462926 PA.
- age_centered: input -0.400000, path term +24.643951 PA.
- work_1: input 471.000000, path term +20.990906 PA.
- op_log_possible_days_upper: input 5.209486, path term +18.060326 PA.
- workload_reference: input 471.000000, path term +16.231124 PA.
- pooled_MLB_K: input 0.210944, path term +10.916308 PA.
Availability path terms: op_log_possible_days_upper +18.060326.

Saved anchor61 head: node reference -100.407580; output -273.904776 (adjustment_target).
After addback, raw PA 197.095224; after bounds/policy 197.095224. Training people 11424.
Largest fitted path terms:
- work_0: input 0.000000, path term -66.231465 PA.
- games_mlb_2: input 102.000000, path term -63.367802 PA.
- workload_reference: input 471.000000, path term -56.016406 PA.
- on_40man: input 1.000000, path term +45.179348 PA.
- quality_0: input 0.000000, path term -13.070662 PA.
- op_log_possible_days_upper: input 5.209486, path term +11.310823 PA.
- games_mlb_0: input 0.000000, path term -8.745630 PA.
- regular_window_scaled: input 0.333333, path term -6.351904 PA.
Availability path terms: op_log_possible_days_upper +11.310823; op_observed_returns +0.003345.

Cutoff-known relevant records:
- Known 2023-03-30, occurred 2023-03-30: Los Angeles Dodgers placed SS Gavin Lux on the 60-day injured list. Right knee surgery..
- Known 2023-11-06, occurred 2023-11-06: Los Angeles Dodgers activated SS Gavin Lux from the 60-day injured list..

Origin-known comparisons, all retained:
- Sheldon Neuse: age 28.0, current/prior MLB PA 0/293, reference 293.00; baseline/direct/anchored 15.92/45.64/85.12, actual 0 PA, 0.000 offense value.
- Aristides Aquino: age 29.0, current/prior MLB PA 0/276, reference 276.00; baseline/direct/anchored 7.87/9.20/15.60, actual 0 PA, 0.000 offense value.
- Bobby Bradley: age 27.0, current/prior MLB PA 0/17, reference 279.11; baseline/direct/anchored 5.19/6.75/39.55, actual 0 PA, 0.000 offense value.
- Kelvin Gutiérrez: age 28.0, current/prior MLB PA 0/33, reference 295.12; baseline/direct/anchored 5.02/3.05/63.16, actual 0 PA, 0.000 offense value.

## Wander Franco at the 2023 cutoff

Selection: fixed diagnostic.
Age 22.0; stage Current MLB; current/prior MLB PA 491/344/308; captured listing 1.
Reference 491.000000 PA; actual workload-profile support 221 distinct training people.
Preserved baseline appearance 0.9899 × conditional PA 548.067 = 542.517 expected PA.
Direct 507.334; anchored 465.421; next-year actual 0 PA.
Fixed hitting estimate 1.035; no realized hitting rate exists because actual PA is zero.
Batting plus replacement: baseline 2.616, direct 2.446, anchored 2.244, actual 0.000.

491 PA/17 HR/69 K and cutoff-known restricted/admin-leave records survive. Anchored reduces expected PA from 542.52 to 465.42; direct gives 507.33, all far above zero actual. The anchored nonmedical path effect is only -2.47 PA while normal quality and roster terms dominate. Generic healthy Gorman/Harris/Greene/Garcia peers are not legal-risk controls. A later permanent ban may not be backdated, but these normal playing-time means are not a satisfactory representation of known unresolved eligibility.

Known source counts:
- 2021 AAA: 180 PA, 7 HR, 21 K, 14 unintentional walks.
- 2021 MLB: 308 PA, 7 HR, 37 K, 24 unintentional walks.
- 2022 AAA: 25 PA, 0 HR, 3 K, 4 unintentional walks.
- 2022 MLB: 344 PA, 6 HR, 33 K, 25 unintentional walks.
- 2022 RK124: 7 PA, 0 HR, 2 K, 0 unintentional walks.
- 2023 MLB: 491 PA, 17 HR, 69 K, 39 unintentional walks.

Workload reference arithmetic:
- 2023: 491 actual PA × 162 / 162.000000 league-average completed games = 491.000000, subject to the declared 800 upper bound.
- 2022: 344 actual PA × 162 / 162.000000 league-average completed games = 344.000000, subject to the declared 800 upper bound.
- 2021: 308 actual PA × 162 / 161.933333 league-average completed games = 308.126801, subject to the declared 800 upper bound.
- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.

Reconstructed pooled count inputs:
- MLB: weighted PA 951.000, K 117.600, HR 26.000; fixed-100 K 0.133777, HR 0.027593. Actual model inputs verified.
- AAA: weighted PA 128.000, K 15.000, HR 4.200; fixed-100 K 0.166667, HR 0.031579. Actual model inputs verified.

Corrected availability inputs:
- op_medical_scope: 1.000000; exposed training people 1105.
- op_recorded_unresolved: 0.000000; exposed training people 19.
- op_log_possible_days_upper: 4.465908; exposed training people 631.
- op_observed_returns: 0.000000; exposed training people 27.
- op_roster_returns: 1.000000; exposed training people 190.
- op_nonmedical_unresolved: 1.000000; exposed training people 31.

Saved direct61 head: node reference 39.126751; output 507.333892 (next_pa).
After addback, raw PA 507.333892; after bounds/policy 507.333892. Training people 11348.
Largest fitted path terms:
- work_0: input 491.000000, path term +262.271099 PA.
- role_mlb_0: input 4.352459, path term +53.732297 PA.
- quality_0: input 0.436266, path term +53.127667 PA.
- age_centered: input -1.000000, path term +42.203790 PA.
- pooled_mlb_quality: input 0.591221, path term +22.261563 PA.
- role_minor_1: input 3.789474, path term -13.975945 PA.
- pooled_MLB_K: input 0.133777, path term +13.760532 PA.
- workload_reference: input 491.000000, path term +11.219959 PA.
Availability path terms: op_log_possible_days_upper +3.575416; op_observed_returns +0.011682.

Saved anchor61 head: node reference -100.836864; output -25.579292 (adjustment_target).
After addback, raw PA 465.420708; after bounds/policy 465.420708. Training people 11348.
Largest fitted path terms:
- quality_0: input 0.436266, path term +46.637102 PA.
- on_40man: input 1.000000, path term +40.155899 PA.
- workload_reference: input 491.000000, path term -24.018510 PA.
- work_0: input 491.000000, path term +21.390856 PA.
- age_centered: input -1.000000, path term +15.654564 PA.
- games_mlb_1: input 83.000000, path term -15.004402 PA.
- pooled_MLB_K: input 0.133777, path term +11.620958 PA.
- regular_window_scaled: input 0.333333, path term -11.325464 PA.
Availability path terms: op_log_possible_days_upper +4.119581; op_nonmedical_unresolved -2.470609; op_observed_returns +0.015851.

Cutoff-known relevant records:
- Known 2022-05-31, occurred 2022-05-31: Tampa Bay Rays placed SS Wander Franco on the 10-day injured list. Right quadriceps strain..
- Known 2022-06-26, occurred 2022-06-26: Tampa Bay Rays activated SS Wander Franco..
- Known 2022-07-10, occurred 2022-07-10: Tampa Bay Rays placed SS Wander Franco on the 10-day injured list. Right wrist discomfort..
- Known 2022-09-09, occurred 2022-09-09: Tampa Bay Rays activated SS Wander Franco from the 10-day injured list..
- Known 2023-08-14, occurred 2023-08-14: Tampa Bay Rays placed SS Wander Franco on the restricted list..
- Known 2023-08-22, occurred 2023-08-22: sourced administrative_leave.

Origin-known comparisons, all retained:
- Nolan Gorman: age 23.0, current/prior MLB PA 464/313, reference 464.00; baseline/direct/anchored 414.06/439.58/379.18, actual 402 PA, 0.279 offense value.
- Michael Harris II: age 22.0, current/prior MLB PA 539/441, reference 539.00; baseline/direct/anchored 532.13/534.85/490.73, actual 470 PA, 1.190 offense value.
- Riley Greene: age 22.0, current/prior MLB PA 416/418, reference 418.00; baseline/direct/anchored 507.98/512.97/452.01, actual 584 PA, 3.490 offense value.
- Luis García Jr.: age 23.0, current/prior MLB PA 482/377, reference 482.00; baseline/direct/anchored 445.28/421.42/399.18, actual 528 PA, 2.013 offense value.

## Wyatt Langford at the 2023 cutoff

Selection: fixed diagnostic.
Age 21.0; stage Upper minors; current/prior MLB PA 0/0/0; captured listing 0.
Reference 100.000000 PA; actual workload-profile support 2430 distinct training people.
Preserved baseline appearance 0.2018 × conditional PA 213.556 = 43.102 expected PA.
Direct 133.226; anchored 102.180; next-year actual 557 PA.
Fixed hitting estimate 0.688 versus observable realized 0.077 per 600 PA.
Batting plus replacement: baseline 0.183, direct 0.565, anchored 0.434, actual 1.796.

All 200 minor PA across four levels remain, including AA 54/4 HR and AAA 26 with six K. The no-MLB workload reference is 100; direct predicts 133.23, anchored 102.18 versus baseline 43.10 and actual 557. AAA/AA usage and age, not medical evidence, raise opportunity. Medical scope is unknown, not healthy. Broad support 2,430 hides rare fast-entry pedigree; Bannister/Veen/Wilken/Morales are age/exposure comparisons rather than equally drafted prospects. Both still severely underproject entry.

Known source counts:
- 2023 AA: 54 PA, 4 HR, 7 K, 11 unintentional walks.
- 2023 AAA: 26 PA, 0 HR, 6 K, 6 unintentional walks.
- 2023 Aplus: 106 PA, 5 HR, 18 K, 18 unintentional walks.
- 2023 RK121: 14 PA, 1 HR, 3 K, 1 unintentional walks.

Workload reference arithmetic:
- 2023: 0 actual PA × 162 / 162.000000 league-average completed games = 0.000000, subject to the declared 800 upper bound.
- 2022: 0 actual PA × 162 / 162.000000 league-average completed games = 0.000000, subject to the declared 800 upper bound.
- 2021: 0 actual PA × 162 / 161.933333 league-average completed games = 0.000000, subject to the declared 800 upper bound.
- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.

Reconstructed pooled count inputs:
- MLB: weighted PA 0.000, K 0.000, HR 0.000; fixed-100 K 0.230000, HR 0.030000. Actual model inputs verified.
- AAA: weighted PA 26.000, K 6.000, HR 0.000; fixed-100 K 0.230159, HR 0.023810. Actual model inputs verified.

Corrected availability inputs:
- op_medical_scope: 0.000000; exposed training people 1128.
- op_recorded_unresolved: 0.000000; exposed training people 20.
- op_log_possible_days_upper: 0.000000; exposed training people 662.
- op_observed_returns: 0.000000; exposed training people 30.
- op_roster_returns: 0.000000; exposed training people 201.
- op_nonmedical_unresolved: 0.000000; exposed training people 26.

Saved direct61 head: node reference 39.268791; output 133.225551 (next_pa).
After addback, raw PA 133.225551; after bounds/policy 133.225551. Training people 11444.
Largest fitted path terms:
- role_pool_AAA: input 4.400000, path term +53.854912 PA.
- age_centered: input -1.200000, path term +26.143518 PA.
- work_0: input 0.000000, path term -21.551640 PA.
- role_pool_AA: input 4.272727, path term +14.916267 PA.
- pooled_AAA_BABIP: input 0.327434, path term +6.498906 PA.
- on_40man: input 0.000000, path term -6.210254 PA.
- pooled_Aplus_2B: input 0.063107, path term +5.858636 PA.
- pooled_AAA_BB: input 0.111111, path term +5.037523 PA.
Availability path terms: op_log_possible_days_upper -0.107239; op_observed_returns +0.003283.

Saved anchor61 head: node reference -100.245751; output 2.179820 (adjustment_target).
After addback, raw PA 102.179820; after bounds/policy 102.179820. Training people 11444.
Largest fitted path terms:
- role_pool_AAA: input 4.400000, path term +39.711643 PA.
- role_pool_AA: input 4.272727, path term +16.528607 PA.
- age_centered: input -1.200000, path term +14.849078 PA.
- pooled_AAA_BABIP: input 0.327434, path term +7.987916 PA.
- pooled_AA_HR: input 0.045455, path term +5.019088 PA.
- games_mlb_2: input 0.000000, path term +4.773258 PA.
- workload_reference: input 100.000000, path term +4.357318 PA.
- on_40man: input 0.000000, path term -4.053522 PA.
Availability path terms: op_log_possible_days_upper -0.071817; op_observed_returns +0.002170.

Cutoff-known relevant records:

Origin-known comparisons, all retained:
- Zion Bannister: age 21.0, current/prior MLB PA 0/0, reference 100.00; baseline/direct/anchored 0.21/4.64/3.98, actual 0 PA, 0.000 offense value.
- Zac Veen: age 21.0, current/prior MLB PA 0/0, reference 100.00; baseline/direct/anchored 85.17/114.11/121.34, actual 0 PA, 0.000 offense value.
- Brock Wilken: age 21.0, current/prior MLB PA 0/0, reference 100.00; baseline/direct/anchored 6.42/1.45/4.19, actual 0 PA, 0.000 offense value.
- Yohandy Morales: age 21.0, current/prior MLB PA 0/0, reference 100.00; baseline/direct/anchored 5.50/1.70/6.40, actual 0 PA, 0.000 offense value.

## Yordan Alvarez at the 2022 cutoff

Selection: fixed diagnostic.
Age 25.0; stage Current MLB; current/prior MLB PA 561/598/9; captured listing 1.
Reference 598.246192 PA; actual workload-profile support 429 distinct training people.
Preserved baseline appearance 0.9896 × conditional PA 516.951 = 511.580 expected PA.
Direct 548.116; anchored 547.378; next-year actual 496 PA.
Fixed hitting estimate 2.814 versus observable realized 5.273 per 600 PA.
Batting plus replacement: baseline 4.001, direct 4.287, anchored 4.281, actual 5.912.

561 PA/37 HR/106 K and prior 598/33 remain. Corrected July reserve-list return closes the stale injury observation; possible absence is a bound. Reference 598.25 plus -50.87 yields 547.38, direct 548.12 versus baseline 511.58 and actual 496. Workload worsens but offense improves because fixed talent 2.814 misses realized 5.273. Positive possible-absence/roster terms are descriptive associations, not proof injury creates playing time. Tucker/Torres and Urias's 177 PA show heterogeneous outcomes.

Known source counts:
- 2020 MLB: 9 PA, 1 HR, 1 K, 0 unintentional walks.
- 2021 MLB: 598 PA, 33 HR, 145 K, 47 unintentional walks.
- 2022 MLB: 561 PA, 37 HR, 106 K, 69 unintentional walks.

Workload reference arithmetic:
- 2022: 561 actual PA × 162 / 162.000000 league-average completed games = 561.000000, subject to the declared 800 upper bound.
- 2021: 598 actual PA × 162 / 161.933333 league-average completed games = 598.246192, subject to the declared 800 upper bound.
- 2020: 9 actual PA × 162 / 59.866667 league-average completed games = 24.354120, subject to the declared 800 upper bound.
- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.

Reconstructed pooled count inputs:
- MLB: weighted PA 1044.800, K 222.600, HR 64.000; fixed-100 K 0.214535, HR 0.058526. Actual model inputs verified.
- AAA: weighted PA 0.000, K 0.000, HR 0.000; fixed-100 K 0.230000, HR 0.030000. Actual model inputs verified.

Corrected availability inputs:
- op_medical_scope: 1.000000; exposed training people 982.
- op_recorded_unresolved: 0.000000; exposed training people 17.
- op_log_possible_days_upper: 3.178054; exposed training people 581.
- op_observed_returns: 0.000000; exposed training people 25.
- op_roster_returns: 1.000000; exposed training people 147.
- op_nonmedical_unresolved: 0.000000; exposed training people 26.

Saved direct61 head: node reference 38.965636; output 548.116440 (next_pa).
After addback, raw PA 548.116440; after bounds/policy 548.116440. Training people 10713.
Largest fitted path terms:
- work_0: input 561.000000, path term +291.834161 PA.
- quality_0: input 1.738114, path term +54.404358 PA.
- role_mlb_0: input 4.144828, path term +37.456893 PA.
- workload_reference: input 598.246192, path term +32.251524 PA.
- age_centered: input -0.400000, path term +18.797755 PA.
- pooled_mlb_quality: input 1.967171, path term +17.188785 PA.
- quality_1: input 0.926630, path term +13.416014 PA.
- on_40man: input 1.000000, path term +10.547572 PA.
Availability path terms: op_log_possible_days_upper +6.187594; op_roster_returns +1.998900; op_observed_returns +0.021704; op_nonmedical_unresolved +0.004552.

Saved anchor61 head: node reference -100.962076; output -50.867790 (adjustment_target).
After addback, raw PA 547.378402; after bounds/policy 547.378402. Training people 10713.
Largest fitted path terms:
- workload_reference: input 598.246192, path term -42.205828 PA.
- on_40man: input 1.000000, path term +37.464903 PA.
- games_mlb_1: input 144.000000, path term -30.694380 PA.
- quality_0: input 1.738114, path term +26.892495 PA.
- regular_window_scaled: input 0.666667, path term -25.813624 PA.
- pooled_MLB_HR: input 0.058526, path term +21.956402 PA.
- quality_1: input 0.926630, path term +21.465945 PA.
- work_0: input 561.000000, path term +17.177983 PA.
Availability path terms: op_log_possible_days_upper +5.484074; op_observed_returns +0.017242; op_nonmedical_unresolved +0.009005.

Cutoff-known relevant records:
- Known 2021-04-14, occurred 2021-04-14: Houston Astros placed 1B Yordan Alvarez on the 10 day injured list..
- Known 2021-04-20, occurred 2021-04-20: Houston Astros activated 1B Yordan Alvarez from the 10-day injured list..
- Known 2021-04-28, occurred 2021-04-28: Houston Astros placed 1B Yordan Alvarez on the 10-day injured list..
- Known 2021-04-30, occurred 2021-04-30: Houston Astros activated 1B Yordan Alvarez from the 10-day injured list..
- Known 2021-04-30, occurred 2021-04-30: Houston Astros activated 1B Yordan Alvarez from the 10-day injured list..
- Known 2021-04-30, occurred 2021-04-30: Houston Astros activated 1B Yordan Alvarez from the 10-day injured list..
- Known 2021-07-05, occurred 2021-07-05: Houston Astros activated 1B Yordan Alvarez from the paternity list..
- Known 2022-04-15, occurred 2022-04-15: Houston Astros placed 1B Yordan Alvarez on the 10-day injured list..
- Known 2022-04-18, occurred 2022-04-18: Houston Astros activated 1B Yordan Alvarez from the 10-day injured list..
- Known 2022-07-10, occurred 2022-07-10: Houston Astros placed 1B Yordan Alvarez on the 10-day injured list. Right hand inflammation..
- Known 2022-07-21, occurred 2022-07-21: Houston Astros activated 1B Yordan Alvarez from the reserve list..

Origin-known comparisons, all retained:
- Ryan Mountcastle: age 25.0, current/prior MLB PA 609/586, reference 609.00; baseline/direct/anchored 494.41/517.18/492.21, actual 470 PA, 2.520 offense value.
- Kyle Tucker: age 25.0, current/prior MLB PA 609/567, reference 616.97; baseline/direct/anchored 560.67/568.37/550.14, actual 674 PA, 5.331 offense value.
- Gleyber Torres: age 25.0, current/prior MLB PA 572/516, reference 572.00; baseline/direct/anchored 508.98/500.55/482.04, actual 672 PA, 4.330 offense value.
- Luis Urías: age 25.0, current/prior MLB PA 472/570, reference 570.23; baseline/direct/anchored 473.82/482.13/484.72, actual 177 PA, 0.389 offense value.

## Joey Votto at the 2016 cutoff

Selection: direct61: largest delivered gain.
Age 32.0; stage Current MLB; current/prior MLB PA 677/695/272; captured listing 1.
Reference 695.286126 PA; actual workload-profile support 52 distinct training people.
Preserved baseline appearance 0.9936 × conditional PA 543.651 = 540.179 expected PA.
Direct 619.440; anchored 638.502; next-year actual 707 PA.
Fixed hitting estimate 2.944 versus observable realized 5.192 per 600 PA.
Batting plus replacement: baseline 4.319, direct 4.952, anchored 5.105, actual 8.301.

Back-to-back 695 and 677 PA/29 HR seasons support the 695.29 reference. Direct predicts 619.44 and anchored 638.50 versus baseline 540.18 and actual 707. Count/use/quality signals, not supported injury terms, explain the actual paths. Both improve workload and offense, though fixed talent still undershoots his actual season. Markakis/Gardner/Cabrera/Cano comparisons retain useful regular use. This is a sensible established-role gain, not proof peak workload is a universal safe prior.

Known source counts:
- 2014 AAA: 6 PA, 0 HR, 2 K, 0 unintentional walks.
- 2014 MLB: 272 PA, 6 HR, 49 K, 45 unintentional walks.
- 2015 MLB: 695 PA, 29 HR, 135 K, 128 unintentional walks.
- 2016 MLB: 677 PA, 29 HR, 120 K, 93 unintentional walks.

Workload reference arithmetic:
- 2016: 677 actual PA × 162 / 161.866667 league-average completed games = 677.557661, subject to the declared 800 upper bound.
- 2015: 695 actual PA × 162 / 161.933333 league-average completed games = 695.286126, subject to the declared 800 upper bound.
- 2014: 272 actual PA × 162 / 162.000000 league-average completed games = 272.000000, subject to the declared 800 upper bound.
- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.

Reconstructed pooled count inputs:
- MLB: weighted PA 1396.200, K 257.400, HR 55.800; fixed-100 K 0.187408, HR 0.039300. Actual model inputs verified.
- AAA: weighted PA 3.600, K 1.200, HR 0.000; fixed-100 K 0.233591, HR 0.028958. Actual model inputs verified.

Corrected availability inputs:
- op_medical_scope: 1.000000; exposed training people 0.
- op_recorded_unresolved: 0.000000; exposed training people 0.
- op_log_possible_days_upper: 0.000000; exposed training people 0.
- op_observed_returns: 0.000000; exposed training people 0.
- op_roster_returns: 0.000000; exposed training people 0.
- op_nonmedical_unresolved: 0.000000; exposed training people 4.

Saved direct61 head: node reference 37.920383; output 619.439566 (next_pa).
After addback, raw PA 619.439566; after bounds/policy 619.439566. Training people 6658.
Largest fitted path terms:
- MLB_0_pa: input 677.000000, path term +199.695839 PA.
- work_0: input 677.557661, path term +83.043774 PA.
- role_mlb_0: input 4.267857, path term +65.041283 PA.
- workload_reference: input 695.286126, path term +44.968038 PA.
- quality_0: input 1.616573, path term +36.775757 PA.
- games_mlb_1: input 158.000000, path term +32.422975 PA.
- regular_window_scaled: input 0.666667, path term +30.619505 PA.
- age_centered: input 1.000000, path term -26.445931 PA.
Availability path terms: none.

Saved anchor61 head: node reference -100.187113; output -56.783703 (adjustment_target).
After addback, raw PA 638.502423; after bounds/policy 638.502423. Training people 6658.
Largest fitted path terms:
- workload_reference: input 695.286126, path term -48.021166 PA.
- on_40man: input 1.000000, path term +37.261980 PA.
- quality_0: input 1.616573, path term +33.063769 PA.
- games_mlb_1: input 158.000000, path term -32.492594 PA.
- pooled_MLB_HR: input 0.039300, path term +14.128380 PA.
- role_mlb_0: input 4.267857, path term +11.963573 PA.
- elapsed_scaled: input 0.900000, path term -11.266081 PA.
- games_mlb_0: input 158.000000, path term +10.373617 PA.
Availability path terms: none.

Cutoff-known relevant records:
- Known 2015-05-09, occurred 2015-05-09: Cincinnati Reds activated 1B Joey Votto..
- Known 2015-09-19, occurred 2015-09-19: Cincinnati Reds activated 1B Joey Votto..

Origin-known comparisons, all retained:
- Nick Markakis: age 32.0, current/prior MLB PA 684/686, reference 710.00; baseline/direct/anchored 513.37/478.73/520.07, actual 670 PA, 2.267 offense value.
- Brett Gardner: age 32.0, current/prior MLB PA 634/656, reference 656.27; baseline/direct/anchored 436.25/430.89/408.60, actual 682 PA, 3.242 offense value.
- Melky Cabrera: age 31.0, current/prior MLB PA 646/683, reference 683.28; baseline/direct/anchored 593.36/623.00/584.07, actual 666 PA, 2.322 offense value.
- Robinson Canó: age 33.0, current/prior MLB PA 715/674, reference 715.59; baseline/direct/anchored 543.35/520.90/549.89, actual 648 PA, 2.935 offense value.

## Yordan Alvarez at the 2024 cutoff

Selection: direct61: false high.
Age 27.0; stage Current MLB; current/prior MLB PA 635/496/561; captured listing 1.
Reference 635.261424 PA; actual workload-profile support 174 distinct training people.
Preserved baseline appearance 0.9886 × conditional PA 560.015 = 553.608 expected PA.
Direct 584.550; anchored 549.976; next-year actual 199 PA.
Fixed hitting estimate 3.746 versus observable realized 1.059 per 600 PA.
Batting plus replacement: baseline 5.186, direct 5.476, anchored 5.152, actual 0.973.

Known 635 PA/35 HR/95 K after 496/31 and 561/37 support substantial use; current recorded medical observation is closed. Direct raises PA 553.61 to 584.55 and anchored gives 549.98 versus only 199 actual, while fixed hitting also exceeds realization. This false high is a plausible major adverse realization under a regular-role mean, not proof the later shortage was knowable at the origin. Naylor/India/Raleigh/Castro comparisons have varied but substantial future use. Mean error and downside uncertainty remain separate.

Known source counts:
- 2022 MLB: 561 PA, 37 HR, 106 K, 69 unintentional walks.
- 2023 AAA: 11 PA, 0 HR, 1 K, 2 unintentional walks.
- 2023 MLB: 496 PA, 31 HR, 92 K, 64 unintentional walks.
- 2024 MLB: 635 PA, 35 HR, 95 K, 53 unintentional walks.

Workload reference arithmetic:
- 2024: 635 actual PA × 162 / 161.933333 league-average completed games = 635.261424, subject to the declared 800 upper bound.
- 2023: 496 actual PA × 162 / 162.000000 league-average completed games = 496.000000, subject to the declared 800 upper bound.
- 2022: 561 actual PA × 162 / 162.000000 league-average completed games = 561.000000, subject to the declared 800 upper bound.
- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.

Reconstructed pooled count inputs:
- MLB: weighted PA 1368.400, K 232.200, HR 82.000; fixed-100 K 0.173795, HR 0.057886. Actual model inputs verified.
- AAA: weighted PA 8.800, K 0.800, HR 0.000; fixed-100 K 0.218750, HR 0.027574. Actual model inputs verified.

Corrected availability inputs:
- op_medical_scope: 1.000000; exposed training people 1191.
- op_recorded_unresolved: 0.000000; exposed training people 21.
- op_log_possible_days_upper: 3.806662; exposed training people 685.
- op_observed_returns: 0.000000; exposed training people 33.
- op_roster_returns: 0.000000; exposed training people 192.
- op_nonmedical_unresolved: 0.000000; exposed training people 31.

Saved direct61 head: node reference 39.296520; output 584.550466 (next_pa).
After addback, raw PA 584.550466; after bounds/policy 584.550466. Training people 11978.
Largest fitted path terms:
- work_0: input 635.261424, path term +315.746542 PA.
- role_mlb_0: input 4.299363, path term +53.153486 PA.
- quality_0: input 1.415653, path term +44.490985 PA.
- workload_reference: input 635.261424, path term +32.283997 PA.
- pooled_mlb_quality: input 2.457089, path term +22.772018 PA.
- quality_1: input 1.383087, path term +17.262553 PA.
- pooled_MLB_HR: input 0.057886, path term +16.209072 PA.
- role_pool_MLB: input 4.278250, path term +13.795093 PA.
Availability path terms: op_log_possible_days_upper +3.114110; op_observed_returns +0.012790; op_roster_returns +0.005181; op_nonmedical_unresolved +0.001831.

Saved anchor61 head: node reference -100.821962; output -85.285461 (adjustment_target).
After addback, raw PA 549.975963; after bounds/policy 549.975963. Training people 11978.
Largest fitted path terms:
- games_mlb_2: input 135.000000, path term -56.403290 PA.
- workload_reference: input 635.261424, path term -42.371204 PA.
- on_40man: input 1.000000, path term +37.729777 PA.
- quality_0: input 1.415653, path term +34.168550 PA.
- work_0: input 635.261424, path term +26.817646 PA.
- work_2: input 561.000000, path term -19.473608 PA.
- pooled_MLB_HR: input 0.057886, path term +18.532818 PA.
- role_mlb_1: input 4.322581, path term -14.379448 PA.
Availability path terms: op_log_possible_days_upper +0.773548; op_observed_returns +0.011946; op_nonmedical_unresolved +0.004056.

Cutoff-known relevant records:
- Known 2023-06-09, occurred 2023-06-09: Houston Astros placed 1B Yordan Alvarez on the 10-day injured list. Right oblique discomfort..
- Known 2023-07-26, occurred 2023-07-26: Houston Astros activated 1B Yordan Alvarez from the 10-day injured list..

Origin-known comparisons, all retained:
- Josh Naylor: age 27.0, current/prior MLB PA 633/495, reference 633.26; baseline/direct/anchored 539.29/544.84/544.95, actual 604 PA, 3.784 offense value.
- Jonathan India: age 27.0, current/prior MLB PA 637/529, reference 637.26; baseline/direct/anchored 554.37/552.18/542.01, actual 567 PA, 1.423 offense value.
- Cal Raleigh: age 27.0, current/prior MLB PA 628/569, reference 628.26; baseline/direct/anchored 485.60/503.03/512.52, actual 705 PA, 6.471 offense value.
- Willi Castro: age 27.0, current/prior MLB PA 635/409, reference 635.26; baseline/direct/anchored 496.45/511.40/528.36, actual 454 PA, 1.128 offense value.

## Aledmys Díaz at the 2021 cutoff

Selection: direct61: ordinary.
Age 30.0; stage Current MLB; current/prior MLB PA 319/59/247; captured listing 1.
Reference 319.131330 PA; actual workload-profile support 188 distinct training people.
Preserved baseline appearance 0.9468 × conditional PA 341.197 = 323.039 expected PA.
Direct 279.128; anchored 251.227; next-year actual 327 PA.
Fixed hitting estimate -0.541 versus observable realized -0.735 per 600 PA.
Batting plus replacement: baseline 0.721, direct 0.623, anchored 0.561, actual 0.624.

319 MLB PA/8 HR, 59 in short 2020 and 247 in 2019 yield reference 319.13. Captured hand injury/July activation remain. Direct 279.13 nearly matches delivered offense, but baseline PA 323.04 is much closer to actual 327; anchored 251.23 worsens both relative to the appropriate component checks. Positive possible-absence path terms are not recovery estimates. Stassi/Heredia/Duffy/Murphy peers include very different next-year roles. Close product is again partly offsetting errors.

Known source counts:
- 2019 AA: 8 PA, 0 HR, 4 K, 2 unintentional walks.
- 2019 AAA: 17 PA, 0 HR, 3 K, 1 unintentional walks.
- 2019 MLB: 247 PA, 9 HR, 28 K, 25 unintentional walks.
- 2020 MLB: 59 PA, 3 HR, 12 K, 1 unintentional walks.
- 2021 AA: 17 PA, 0 HR, 3 K, 4 unintentional walks.
- 2021 MLB: 319 PA, 8 HR, 62 K, 13 unintentional walks.
- 2021 RK124: 6 PA, 0 HR, 1 K, 1 unintentional walks.

Workload reference arithmetic:
- 2021: 319 actual PA × 162 / 161.933333 league-average completed games = 319.131330, subject to the declared 800 upper bound.
- 2020: 59 actual PA × 162 / 59.866667 league-average completed games = 159.654788, subject to the declared 800 upper bound.
- 2019: 247 actual PA × 162 / 161.933333 league-average completed games = 247.101688, subject to the declared 800 upper bound.
- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.

Reconstructed pooled count inputs:
- MLB: weighted PA 514.400, K 88.400, HR 15.800; fixed-100 K 0.181315, HR 0.030599. Actual model inputs verified.
- AAA: weighted PA 10.200, K 1.800, HR 0.000; fixed-100 K 0.225045, HR 0.027223. Actual model inputs verified.

Corrected availability inputs:
- op_medical_scope: 1.000000; exposed training people 915.
- op_recorded_unresolved: 0.000000; exposed training people 14.
- op_log_possible_days_upper: 4.430817; exposed training people 520.
- op_observed_returns: 0.000000; exposed training people 30.
- op_roster_returns: 1.000000; exposed training people 23.
- op_nonmedical_unresolved: 0.000000; exposed training people 22.

Saved direct61 head: node reference 38.198968; output 279.127524 (next_pa).
After addback, raw PA 279.127524; after bounds/policy 279.127524. Training people 9957.
Largest fitted path terms:
- work_0: input 319.131330, path term +194.650176 PA.
- on_40man: input 1.000000, path term +40.834709 PA.
- quality_0: input -0.041283, path term -16.132741 PA.
- op_log_possible_days_upper: input 4.430817, path term +14.132000 PA.
- pooled_MLB_K: input 0.181315, path term +13.198526 PA.
- role_mlb_0: input 3.819149, path term -11.471415 PA.
- MLB_0_pa: input 319.000000, path term +7.971588 PA.
- pooled_MLB_BB: input 0.059896, path term +5.940871 PA.
Availability path terms: op_log_possible_days_upper +14.132000.

Saved anchor61 head: node reference -100.455496; output -67.903858 (adjustment_target).
After addback, raw PA 251.227472; after bounds/policy 251.227472. Training people 9957.
Largest fitted path terms:
- on_40man: input 1.000000, path term +42.635685 PA.
- workload_reference: input 319.131330, path term -19.933541 PA.
- games_mlb_2: input 69.000000, path term -14.589328 PA.
- op_log_possible_days_upper: input 4.430817, path term +10.774581 PA.
- work_0: input 319.131330, path term +9.622252 PA.
- quality_0: input -0.041283, path term -7.874801 PA.
- pooled_MLB_BB: input 0.059896, path term +7.170442 PA.
- games_pool_MLB: input 162.120000, path term -6.301626 PA.
Availability path terms: op_log_possible_days_upper +10.774581.

Cutoff-known relevant records:
- Known 2020-07-25, occurred 2020-07-25: Houston Astros placed 2B Aledmys Diaz on the 10-day injured list. Right groin strain..
- Known 2020-08-29, occurred 2020-08-29: Houston Astros activated 2B Aledmys Diaz from the 10-day injured list..
- Known 2020-08-29, occurred 2020-08-29: Houston Astros activated SS Aledmys Diaz from the 10 day injured list..
- Known 2020-08-29, occurred 2020-08-29: Houston Astros activated SS Aledmys Diaz from the 10-day injured list..
- Known 2021-06-08, occurred 2021-06-06: Houston Astros placed SS Aledmys Diaz on the 10-day injured list. Left hand fracture..
- Known 2021-07-26, occurred 2021-07-26: Houston Astros activated SS Aledmys Diaz..

Origin-known comparisons, all retained:
- Max Stassi: age 30.0, current/prior MLB PA 319/105, reference 319.13; baseline/direct/anchored 276.48/286.97/251.26, actual 375 PA, -0.597 offense value.
- Guillermo Heredia: age 30.0, current/prior MLB PA 347/36, reference 347.14; baseline/direct/anchored 216.95/216.06/219.69, actual 82 PA, -0.221 offense value.
- Matt Duffy: age 30.0, current/prior MLB PA 322/0, reference 322.13; baseline/direct/anchored 150.41/175.88/180.49, actual 247 PA, 0.067 offense value.
- Tom Murphy: age 30.0, current/prior MLB PA 325/0, reference 325.13; baseline/direct/anchored 197.10/228.49/191.83, actual 42 PA, 0.391 offense value.

## Jorge Soler at the 2018 cutoff

Selection: anchor61: largest delivered harm.
Age 26.0; stage Current MLB; current/prior MLB PA 257/110/264; captured listing 1.
Reference 264.217463 PA; actual workload-profile support 304 distinct training people.
Preserved baseline appearance 0.9566 × conditional PA 383.742 = 367.083 expected PA.
Direct 367.606; anchored 220.163; next-year actual 679 PA.
Fixed hitting estimate 0.456 versus observable realized 3.565 per 600 PA.
Batting plus replacement: baseline 1.409, direct 1.411, anchored 0.845, actual 6.125.

MLB PA 257/110/264 and AAA 327 PA/24 HR in 2017 survive together with toe fracture and November activation. Reference only 264.22 plus -44.05 gives 220.16 PA, well below baseline/direct about 367 and actual 679. Fixed batting talent also misses the power breakout. The anchored model understates growth beyond a limited prior workload; older-game and rare AAA triple-rate path terms hurt despite current quality/roster signals. Broad profile count 304 and catcher/backup comparison players are not equivalent power/job profiles. This is a substantive lost opportunity, not a harmless tiny subgroup tradeoff.

Known source counts:
- 2016 AA: 42 PA, 0 HR, 11 K, 11 unintentional walks.
- 2016 AAA: 7 PA, 0 HR, 5 K, 0 unintentional walks.
- 2016 MLB: 264 PA, 12 HR, 66 K, 31 unintentional walks.
- 2017 AAA: 327 PA, 24 HR, 82 K, 50 unintentional walks.
- 2017 MLB: 110 PA, 2 HR, 36 K, 11 unintentional walks.
- 2018 AAA: 10 PA, 0 HR, 6 K, 2 unintentional walks.
- 2018 MLB: 257 PA, 9 HR, 69 K, 28 unintentional walks.

Workload reference arithmetic:
- 2018: 257 actual PA × 162 / 162.066667 league-average completed games = 256.894282, subject to the declared 800 upper bound.
- 2017: 110 actual PA × 162 / 162.000000 league-average completed games = 110.000000, subject to the declared 800 upper bound.
- 2016: 264 actual PA × 162 / 161.866667 league-average completed games = 264.217463, subject to the declared 800 upper bound.
- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.

Reconstructed pooled count inputs:
- MLB: weighted PA 503.400, K 137.400, HR 17.800; fixed-100 K 0.265827, HR 0.034471. Actual model inputs verified.
- AAA: weighted PA 275.800, K 74.600, HR 19.200; fixed-100 K 0.259713, HR 0.059074. Actual model inputs verified.

Corrected availability inputs:
- op_medical_scope: 1.000000; exposed training people 682.
- op_recorded_unresolved: 0.000000; exposed training people 13.
- op_log_possible_days_upper: 5.129899; exposed training people 324.
- op_observed_returns: 0.000000; exposed training people 15.
- op_roster_returns: 0.000000; exposed training people 13.
- op_nonmedical_unresolved: 0.000000; exposed training people 12.

Saved direct61 head: node reference 37.936327; output 367.606184 (next_pa).
After addback, raw PA 367.606184; after bounds/policy 367.606184. Training people 8222.
Largest fitted path terms:
- work_0: input 256.894282, path term +92.021213 PA.
- quality_0: input 0.376159, path term +84.153130 PA.
- on_40man: input 1.000000, path term +54.479674 PA.
- role_mlb_0: input 4.183099, path term +37.610569 PA.
- MLB_0_pa: input 257.000000, path term +32.725662 PA.
- pooled_mlb_quality: input 0.162286, path term +18.675895 PA.
- role_pool_AAA: input 4.361878, path term +16.336525 PA.
- pooled_AAA_HR: input 0.059074, path term +15.396869 PA.
Availability path terms: op_log_possible_days_upper +14.461470.

Saved anchor61 head: node reference -100.022674; output -44.054307 (adjustment_target).
After addback, raw PA 220.163156; after bounds/policy 220.163156. Training people 8222.
Largest fitted path terms:
- quality_0: input 0.376159, path term +68.022293 PA.
- games_mlb_2: input 86.000000, path term -40.090210 PA.
- on_40man: input 1.000000, path term +39.605660 PA.
- pooled_AAA_3B: input 0.001330, path term -21.384858 PA.
- draft_rank: input 0.000000, path term -13.574873 PA.
- role_pool_AAA: input 4.361878, path term +11.813646 PA.
- pooled_AAA_HR: input 0.059074, path term +10.782281 PA.
- role_pool_AA: input 4.233766, path term +10.507106 PA.
Availability path terms: op_log_possible_days_upper +7.773952.

Cutoff-known relevant records:
- Known 2017-04-02, occurred 2017-03-30: Kansas City Royals placed LF Jorge Soler on the 10-day disabled list retroactive to March 30, 2017. Strained left oblique..
- Known 2017-07-17, occurred 2017-07-17: Kansas City Royals recalled Jorge Soler from Omaha Storm Chasers..
- Known 2017-09-05, occurred 2017-09-05: Kansas City Royals recalled RF Jorge Soler from Omaha Storm Chasers..
- Known 2018-06-17, occurred 2018-06-16: Kansas City Royals placed RF Jorge Soler on the 10-day disabled list retroactive to June 16, 2018. Left toe fracture..
- Known 2018-08-12, occurred 2018-08-12: Kansas City Royals transferred RF Jorge Soler from the 10-day disabled list to the 60-day disabled list. Left toe fracture..
- Known 2018-11-02, occurred 2018-11-02: Kansas City Royals activated RF Jorge Soler from the 60-day injured list..

Origin-known comparisons, all retained:
- Kevin Plawecki: age 27.0, current/prior MLB PA 277/118, reference 276.89; baseline/direct/anchored 226.35/238.41/233.37, actual 174 PA, 0.050 offense value.
- Luke Maile: age 27.0, current/prior MLB PA 231/136, reference 230.90; baseline/direct/anchored 156.19/198.65/180.79, actual 129 PA, -0.860 offense value.
- Andrew Knapp: age 26.0, current/prior MLB PA 215/204, reference 214.91; baseline/direct/anchored 169.10/157.78/161.15, actual 160 PA, 0.038 offense value.
- Jefry Marte: age 27.0, current/prior MLB PA 209/145, reference 284.23; baseline/direct/anchored 71.54/87.06/76.89, actual 0 PA, 0.000 offense value.

## Ronald Acuña Jr. at the 2023 cutoff

Selection: anchor61: false high.
Age 25.0; stage Current MLB; current/prior MLB PA 735/533/360; captured listing 1.
Reference 735.000000 PA; actual workload-profile support 165 distinct training people.
Preserved baseline appearance 0.9924 × conditional PA 586.899 = 582.426 expected PA.
Direct 600.143; anchored 634.035; next-year actual 222 PA.
Fixed hitting estimate 3.414 versus observable realized 0.251 per 600 PA.
Batting plus replacement: baseline 5.117, direct 5.272, anchored 5.570, actual 0.780.

735 PA/41 HR/84 K after 533 and 360 PA support a high workload mean. Reference 735 plus -100.96 gives 634.04 versus baseline 582.43, direct 600.14 and actual 222. Prior ACL history is in captured evidence, but the model did not know the later short season. Both workload and fixed hitting overpredict, increasing delivered-value error. Rutschman/Kwan/Hoerner/Torres comparisons remain useful regulars. Anchor optimism improves some durable stars while increasing genuine injury/downside misses.

Known source counts:
- 2021 MLB: 360 PA, 24 HR, 85 K, 47 unintentional walks.
- 2022 AAA: 25 PA, 0 HR, 6 K, 5 unintentional walks.
- 2022 MLB: 533 PA, 15 HR, 126 K, 49 unintentional walks.
- 2023 MLB: 735 PA, 41 HR, 84 K, 77 unintentional walks.

Workload reference arithmetic:
- 2023: 735 actual PA × 162 / 162.000000 league-average completed games = 735.000000, subject to the declared 800 upper bound.
- 2022: 533 actual PA × 162 / 162.000000 league-average completed games = 533.000000, subject to the declared 800 upper bound.
- 2021: 360 actual PA × 162 / 161.933333 league-average completed games = 360.148209, subject to the declared 800 upper bound.
- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.

Reconstructed pooled count inputs:
- MLB: weighted PA 1377.400, K 235.800, HR 67.400; fixed-100 K 0.175173, HR 0.047651. Actual model inputs verified.
- AAA: weighted PA 20.000, K 4.800, HR 0.000; fixed-100 K 0.231667, HR 0.025000. Actual model inputs verified.

Corrected availability inputs:
- op_medical_scope: 1.000000; exposed training people 1121.
- op_recorded_unresolved: 0.000000; exposed training people 16.
- op_log_possible_days_upper: 3.135494; exposed training people 662.
- op_observed_returns: 0.000000; exposed training people 33.
- op_roster_returns: 0.000000; exposed training people 193.
- op_nonmedical_unresolved: 0.000000; exposed training people 31.

Saved direct61 head: node reference 38.986315; output 600.143444 (next_pa).
After addback, raw PA 600.143444; after bounds/policy 600.143444. Training people 11424.
Largest fitted path terms:
- work_0: input 735.000000, path term +313.899829 PA.
- quality_0: input 2.072838, path term +52.125904 PA.
- role_mlb_0: input 4.585799, path term +47.780365 PA.
- workload_reference: input 735.000000, path term +43.826340 PA.
- age_centered: input -0.400000, path term +29.886436 PA.
- role_pool_MLB: input 4.522655, path term +18.027999 PA.
- pooled_MLB_K: input 0.175173, path term +14.972003 PA.
- pooled_mlb_quality: input 2.173401, path term +14.444065 PA.
Availability path terms: op_log_possible_days_upper +4.351332.

Saved anchor61 head: node reference -100.407580; output -100.964787 (adjustment_target).
After addback, raw PA 634.035213; after bounds/policy 634.035213. Training people 11424.
Largest fitted path terms:
- games_mlb_2: input 82.000000, path term -67.607988 PA.
- workload_reference: input 735.000000, path term -60.303070 PA.
- on_40man: input 1.000000, path term +35.607816 PA.
- quality_0: input 2.072838, path term +34.802193 PA.
- work_0: input 735.000000, path term +34.486610 PA.
- age_centered: input -0.400000, path term +9.921901 PA.
- role_mlb_0: input 4.585799, path term +7.626296 PA.
- pooled_MLB_K: input 0.175173, path term +7.093836 PA.
Availability path terms: op_log_possible_days_upper +2.316015; op_observed_returns +0.003345.

Cutoff-known relevant records:
- Known 2022-04-04, occurred 2022-04-04: Atlanta Braves placed LF Ronald Acuna Jr. on the 10-day injured list. Recovering from Right ACL Tear..
- Known 2022-04-28, occurred 2022-04-28: Atlanta Braves activated LF Ronald Acuña Jr. from the 10-day injured list..

Origin-known comparisons, all retained:
- Adley Rutschman: age 25.0, current/prior MLB PA 687/470, reference 687.00; baseline/direct/anchored 599.91/620.05/605.88, actual 638 PA, 1.434 offense value.
- Steven Kwan: age 25.0, current/prior MLB PA 718/638, reference 718.00; baseline/direct/anchored 573.73/566.40/613.60, actual 540 PA, 3.059 offense value.
- Nico Hoerner: age 26.0, current/prior MLB PA 688/517, reference 688.00; baseline/direct/anchored 527.68/543.65/560.58, actual 641 PA, 1.752 offense value.
- Gleyber Torres: age 26.0, current/prior MLB PA 672/572, reference 672.00; baseline/direct/anchored 549.13/571.07/580.47, actual 665 PA, 1.756 offense value.

## Kevin Pillar at the 2022 cutoff

Selection: anchor61: ordinary.
Age 33.0; stage Current MLB; current/prior MLB PA 13/347/223; captured listing 0.
Reference 603.440980 PA; actual workload-profile support 31 distinct training people.
Preserved baseline appearance 0.3546 × conditional PA 139.683 = 49.532 expected PA.
Direct 64.189; anchored 154.418; next-year actual 206 PA.
Fixed hitting estimate -1.117 versus observable realized -1.313 per 600 PA.
Batting plus replacement: baseline 0.063, direct 0.082, anchored 0.196, actual 0.194.

223 PA in short 2020 annualizes to a 603.44 reference; that is not an observed 603-PA season. Current 13 MLB PA and AAA 176/10 HR/22 K, previous 347 MLB PA, age 33 and shoulder-fracture records all remain. Adjustment -449.02 leaves 154.42 versus baseline 49.53, direct 64.19 and actual 206. The large correction prevents assigning the reference as a starting role. Nearly exact offense still combines understated workload and an overoptimistic rate. Upton/Gosselin non-arrivals, Ahmed's 210 and La Stella's 24 show downside among prior regulars.

Known source counts:
- 2020 MLB: 223 PA, 6 HR, 41 K, 12 unintentional walks.
- 2021 MLB: 347 PA, 15 HR, 81 K, 11 unintentional walks.
- 2022 AAA: 176 PA, 10 HR, 22 K, 20 unintentional walks.
- 2022 MLB: 13 PA, 0 HR, 4 K, 1 unintentional walks.

Workload reference arithmetic:
- 2022: 13 actual PA × 162 / 162.000000 league-average completed games = 13.000000, subject to the declared 800 upper bound.
- 2021: 347 actual PA × 162 / 161.933333 league-average completed games = 347.142857, subject to the declared 800 upper bound.
- 2020: 223 actual PA × 162 / 59.866667 league-average completed games = 603.440980, subject to the declared 800 upper bound.
- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.

Reconstructed pooled count inputs:
- MLB: weighted PA 424.400, K 93.400, HR 15.600; fixed-100 K 0.221968, HR 0.035469. Actual model inputs verified.
- AAA: weighted PA 176.000, K 22.000, HR 10.000; fixed-100 K 0.163043, HR 0.047101. Actual model inputs verified.

Corrected availability inputs:
- op_medical_scope: 1.000000; exposed training people 1000.
- op_recorded_unresolved: 0.000000; exposed training people 17.
- op_log_possible_days_upper: 4.927254; exposed training people 612.
- op_observed_returns: 0.000000; exposed training people 34.
- op_roster_returns: 0.000000; exposed training people 154.
- op_nonmedical_unresolved: 0.000000; exposed training people 26.

Saved direct61 head: node reference 39.883232; output 64.189316 (next_pa).
After addback, raw PA 64.189316; after bounds/policy 64.189316. Training people 10877.
Largest fitted path terms:
- workload_reference: input 603.440980, path term +42.577180 PA.
- on_40man: input 0.000000, path term -25.102387 PA.
- age_centered: input 1.200000, path term -22.391193 PA.
- work_0: input 13.000000, path term -15.999294 PA.
- op_log_possible_days_upper: input 4.927254, path term +11.814920 PA.
- work_1: input 347.142857, path term +8.958319 PA.
- role_pool_AAA: input 4.153846, path term +8.273510 PA.
- pooled_MLB_BB: input 0.047674, path term +6.413340 PA.
Availability path terms: op_log_possible_days_upper +11.814920; op_observed_returns +0.005168.

Saved anchor61 head: node reference -100.188113; output -449.023077 (adjustment_target).
After addback, raw PA 154.417903; after bounds/policy 154.417903. Training people 10877.
Largest fitted path terms:
- workload_reference: input 603.440980, path term -86.065301 PA.
- work_0: input 13.000000, path term -65.854927 PA.
- games_mlb_2: input 145.800000, path term -62.766057 PA.
- on_40man: input 0.000000, path term -62.133394 PA.
- role_mlb_0: input 3.785714, path term -16.457096 PA.
- games_minor_0: input 42.000000, path term -15.666271 PA.
- pooled_mlb_quality: input -0.103754, path term -10.576971 PA.
- op_log_possible_days_upper: input 4.927254, path term +9.091624 PA.
Availability path terms: op_log_possible_days_upper +9.091624; op_observed_returns +0.005921.

Cutoff-known relevant records:
- Known 2021-02-21, occurred 2021-02-21: New York Mets signed free agent CF Kevin Pillar..
- Known 2021-02-21, occurred 2021-02-21: New York Mets signed free agent CF Kevin Pillar..
- Known 2021-02-21, occurred 2021-02-21: New York Mets signed free agent CF Kevin Pillar..
- Known 2021-02-21, occurred 2021-02-21: New York Mets signed free agent CF Kevin Pillar..
- Known 2021-02-21, occurred 2021-02-21: New York Mets signed free agent CF Kevin Pillar..
- Known 2021-05-18, occurred 2021-05-18: New York Mets placed CF Kevin Pillar on the 10-day injured list. Multiple facial fractures..
- Known 2021-05-31, occurred 2021-05-31: New York Mets activated CF Kevin Pillar from the 10-day injured list..
- Known 2022-05-28, occurred 2022-05-28: Los Angeles Dodgers selected the contract of CF Kevin Pillar from Oklahoma City Dodgers..
- Known 2022-06-02, occurred 2022-06-02: Los Angeles Dodgers placed CF Kevin Pillar on the 10-day injured list. Left shoulder fracture..
- Known 2022-06-03, occurred 2022-06-03: Los Angeles Dodgers transferred CF Kevin Pillar from the 10-day injured list to the 60-day injured list. Left shoulder fracture..

Origin-known comparisons, all retained:
- Justin Upton: age 34.0, current/prior MLB PA 57/362, reference 449.20; baseline/direct/anchored 11.73/15.13/45.15, actual 0 PA, 0.000 offense value.
- Phil Gosselin: age 33.0, current/prior MLB PA 77/373, reference 373.15; baseline/direct/anchored 30.97/13.16/48.93, actual 0 PA, 0.000 offense value.
- Nick Ahmed: age 32.0, current/prior MLB PA 54/473, reference 587.20; baseline/direct/anchored 156.77/194.99/258.04, actual 210 PA, -0.363 offense value.
- Tommy La Stella: age 33.0, current/prior MLB PA 195/242, reference 616.97; baseline/direct/anchored 62.90/65.81/131.34, actual 24 PA, -0.038 offense value.

## Decision after review

Neither global replacement improves the complete forecast enough to adopt. The absence-group gain is real development evidence,
but Lux worsens, McLain remains materially underprojected and sparse elite/medical profiles remain. Established-role use differs
from brief-debut growth; lost Soler/Judge opportunity and adverse Acuna/Yordan outcomes prevent a universal-reference upgrade.
Keep the source correction and saved comparison. Do not tune the reference floor or peak definition to these names.
The corrected baseline remains default; no protected 2026 forecast or deployed explorer changed.
