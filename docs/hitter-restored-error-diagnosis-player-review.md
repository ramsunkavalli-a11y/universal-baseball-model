# Player checks for hitting and playing time error

2026-10-05. All seventeen cases remain from the completed seven-input comparison;
no player, fit, source, outcome or comparison peer was replaced. This review adds
exact error accounting to the actual [source and fitted model walks](hitter-mlb-events-restoration-player-review.md).
Their public machine report preserves raw annual MLB/minor/foreign counts,
denominators, adjustments, all fitted terms, removal probes, joint training support
and three origin-selected earlier peers. The new report references that exact
report and case ID with its hash. This is not a new fit or independent validation.

## Meaning of the numbers

Rates are future MLB batting wins above league mean per 600 PA. Delivered value
adds replacement at expected PA, not defense or full WAR. In the table, hitting
error is `expected PA * (forecast rate - actual rate) / 600`; opportunity error
is `(expected PA - actual PA) * (actual rate / 600 + replacement)`. Their sum is
the newer delivered error. Positive means overprediction, negative underprediction.
Non-arrivals have no actual hitting rate and no such active-player decomposition.

| Case and row | Expected and actual PA | New hitting error | Common opportunity error | New delivered error |
| --- | ---: | ---: | ---: | ---: |
| Judge 2016, 23934 | 309.9 / 678 | −2.8970 | −4.4054 | −7.3024 |
| Thames 2017, 27981 | 444.4 / 278 | +1.8225 | +0.6843 | +2.5068 |
| Maitan 2017, 31364 | 2.0 / 0 | Unobserved | Not decomposed | +0.0051 |
| Davis 2018, 32325 | 572.8 / 533 | +3.7422 | +0.0218 | +3.7641 |
| Wilkerson 2018, 32754 | 109.5 / 361 | +0.0496 | −0.0829 | −0.0333 |
| France 2018, 34339 | 87.0 / 201 | +0.1493 | −0.1497 | −0.0004 |
| Alvarez 2018, 35088 | 72.2 / 369 | −0.6235 | −3.7083 | −4.3318 |
| Nola 2021, 42235 | 245.9 / 397 | +0.2835 | −0.2407 | +0.0428 |
| Tatis 2021, 43296 | 553.0 / 0 | Unobserved | Not decomposed | +4.7012 |
| Suzuki 2022, 47765 | 406.3 / 583 | +0.3768 | −1.1415 | −0.7647 |
| Judge 2023, 50698 | 536.0 / 704 | −3.4027 | −2.6363 | −6.0390 |
| Misner 2024, 55509 | 84.5 / 217 | −0.0065 | +0.0335 | +0.0271 |
| Perdomo 2024, 55587 | 472.6 / 720 | −2.6816 | −1.8974 | −4.5790 |
| Kurtz 2024, 57052 | 10.2 / 489 | −0.0767 | −5.6051 | −5.6818 |
| Yoshida 2024, 57778 | 476.2 / 205 | +1.4577 | +0.6464 | +2.1041 |
| Lee 2024, 58061 | 153.6 / 617 | +0.2482 | −1.8046 | −1.5564 |
| Suzuki 2021 addition, 63309 | 191.5 / 446 | +0.6829 | −1.2958 | −0.6130 |

The origin in each name is the last input season; the forecast is for the next
calendar season. A small hitting term at very low expected PA does not imply
good conditional talent accuracy. All seventeen baseline-plus-residual and
intercept-plus-feature equations verify against the saved forecasts.

## Judge before the breakout and as an established star

Judge 2016, row 23934, cutoff 2017-01-28, fold 3 tracking: 95 MLB PA with
four HR and 42 K accompany 410 AAA PA with 19 HR and 98 K. The prior-shrunk K
term is −0.049112; all added terms total −0.032934. Baseline −0.726057 plus
residual +0.447427 gives −0.278630, below incumbent +0.264151 and actual
+5.329876. Hitting and PA errors reinforce each other. Delivered squared error
increases 4.016097 versus incumbent and 0.184865 versus matched. Support is 6/5
distinct full/active people; the d'Arnaud, Alonso and Taylor peers are unchanged.
This is a missed breakout with real poor debut evidence, not proof to discard K.

Judge 2023, row 50698, cutoff 2024-01-26, fold 3 tracking: recent MLB seasons
have 458/696/633 PA and 37/62/39 HR. Baseline +2.756953 plus residual +0.991670
gives +3.748623, below incumbent +3.898807 and actual +7.557649. Added effects
+0.092994 are more than offset by old coefficient change −0.118361. Both rate
and PA miss low; squared delivered error worsens 1.602442 versus incumbent and
0.273195 versus matched. Support remains 19/19; Stanton, Frazier and Alonso
comparisons include weaker subsequent seasons. This mature-MLB loss cannot be
explained by foreign history or a missing rookie batting label.

## Thames and Yoshida reinforce both errors

Thames, row 27981, cutoff 2018-01-27, fold 4 tracking: 551 MLB PA with 31 HR,
163 K and 70 walks accompany older KBO 40/47-HR seasons. Baseline +3.149685
plus residual −0.066352 gives +3.083333 versus incumbent +0.370179, matched
+3.069216 and actual +0.622421. The seven new effects are only +0.026389;
the optimistic baseline is already present. Hitting overprediction +1.8225
and excessive PA +0.6843 reinforce. Squared error worsens 6.036611 versus
incumbent, 0.052305 versus matched. Support is 0/0; Kang succeeds, Park is absent
and Hyun Soo Kim fails in the unchanged peers. Foreign-removal sensitivity
−2.396396 diagnoses model dependence, not a validated replacement forecast.

Yoshida, row 57778, cutoff 2025-01-24, fold 3 tracking: 421/580 MLB PA with
10/15 HR retain 304.8 recency-weighted NPB PA. Baseline +1.596821 plus residual
−0.204012 gives +1.392809 versus incumbent +0.326683 and actual −0.443798.
Added low-K effects raise the rate, net +0.029748 versus matched. Both errors
are positive; squared error worsens 2.844854 incumbent and 0.098802 matched.
Support remains 0/0; Aoki, Suzuki and absent Brosseau remain the comparisons.
These cases flag provisional foreign adaptation, not the cause of the mature
domestic group's much larger aggregate contribution.

## Suzuki and Lee show opposite cancellation traps

Suzuki 2022, row 47765, cutoff 2023-01-26, fold 1 tracking: 446 MLB PA with
14 HR/110 K retain 734.8 weighted NPB PA. Baseline +2.577305 plus residual
−0.024137 gives +2.553168, versus incumbent +0.160076, matched +2.598622 and
actual +1.996717. The seven terms lower hitting by −0.037483, with old change
−0.007971. Compared with matched, the squared hitting term improves −0.024140,
but interaction worsens +0.070263; delivered squared error worsens +0.046123.
Compared with incumbent both errors improve substantially overall. The forecast
still compensates partly for 406.3 versus 583 PA. Support is 2/1; Tsutsugo,
Evans and Clark do not provide strong positive peer confirmation.

Lee, row 58061, cutoff 2025-01-24, fold 1 tracking: 158 MLB PA with two HR/
13 K retain 685.8 weighted KBO PA. Baseline +1.839976 plus residual −0.407633
gives +1.432342 versus matched +1.311113 and actual +0.463100. Added low-K
effects +0.182963 outweigh old change −0.061733. Against matched, squared
hitting error worsens +0.014447 while interaction improves −0.112047, producing
delivered improvement −0.097600. The improvement masks optimistic hitting and
153.6 versus 617 PA. Support is 0/0; Ha Seong Kim's modest success, absent Hwang
and absent Hyun Soo Kim remain. Do not call the matched change a talent win.

Suzuki 2021 addition, row 63309, cutoff 2022-03-18, fold 1 prospect: 1,659
NPB PA, 1,311.4 weighted, produce baseline +3.920524 plus residual −0.606153
= +3.314371. Actual +1.174589 is lower, but 191.5 forecast versus 446 actual PA
offsets the excessive rate. Against matched, hitting squared error improves
−0.026689, interaction worsens +0.049941, net delivered worsens +0.023252.
There is no incumbent comparison. Support is 2/0; Rosario, Nakajima and Meneses
are all absent. Source correctness does not demonstrate transfer calibration.

## Davis and Perdomo retain different mature MLB misses

Davis, row 32325, cutoff 2019-01-27, fold 3 tracking: three MLB seasons of
654/652/610 PA and 48/43/42 HR give baseline +1.428279 plus residual +0.973317
= +2.401596. Actual −1.518480 is far lower. Seven effects +0.019479 and old
change −0.039666 slightly improve matched, but remain worse than incumbent
+2.287559. Almost all delivered error is hitting: +3.7422 versus +0.0218 PA.
Squared error changes are +0.807687 incumbent and −0.145444 matched. Support
9/9 and the Frazier, Dozier and Morales peers remain. A reasonable strong prior
season can miss a collapse; neither the source nor the absence of foreign data
explains away the forecast error.

Perdomo, row 55587, cutoff 2025-01-24, fold 1 tracking: recent 388/495/500 MLB
PA with 3/6/5 HR give baseline −0.264995 plus residual −0.411615 = −0.676609.
Actual +2.727891 and 720 PA exceed every arm. Added effects +0.155603 are mostly
offset by old change −0.139072. Both errors remain negative; squared delivered
error improves −1.891288 incumbent and −0.119418 matched. Support 60/55 is more
substantial, but Thole, Brantley and Schafer peers are not all breakout hitters.
This is a small mechanistic improvement, not an identified superstar forecast.

## Misner helps while ordinary cases require caution

Misner, row 55509, cutoff 2025-01-24, fold 3 tracking: ten K in fifteen MLB PA
sit beside two 519-PA AAA seasons. Baseline −0.733207 plus residual −1.338370
gives −2.071577 versus matched −1.959387, incumbent −1.840052 and actual
−2.025635. Added effects −0.124284 plus old change +0.012094 correct the rate.
Delivered error falls from +0.059685 incumbent to +0.027068. Expected PA remains
84.5 versus 217 actual; at observed below-replacement hitting the low PA creates
a positive opportunity term. Support 641/422 and Harrison, Deichmann and Tucker
comparisons remain. The rate slightly overshoots; favorable value is not perfect PA.

Wilkerson, row 32754, cutoff 2019-01-27, fold 3 tracking: 49 MLB PA with sixteen
K and zero HR join mixed AAA/AA/rookie history. Baseline −1.112917 plus residual
−0.265761 = −1.378678 moves toward actual −1.650306. Seven effects −0.030121
plus old change +0.011193 improve hitting, but remove favorable offset against
109.5 versus 361 PA. Squared delivered error worsens +0.000822 incumbent and
+0.000218 matched. Support 341/209 and Martinez, Mejia and Perkins peers stay.

France, row 34339, cutoff 2019-01-27, fold 1 prospect: 479 AA/110 AAA PA,
17/5 HR and 25/2 HBP provide no MLB inputs. Baseline −0.964989 plus residual
+0.934448 = −0.030541; actual −1.059985 is worse. Added effects are zero, other
change −0.005681. Hitting error +0.149284 almost exactly cancels opportunity
−0.149716. The near-zero delivered error is not a clean success; the incumbent
has less hitting error even though its delivered error is larger. Support
1,444/326 and absent Bandy, Puello and Pohl peers are unchanged.

Nola, row 42235, cutoff 2022-03-18, fold 2 tracking: MLB 194/184/267 PA and
2/7/10 HR include the short 2020 season. Baseline +0.610894 plus residual
−0.843750 = −0.232856 versus actual −0.924711. Added effects +0.070563 plus
old change −0.036436 make hitting more optimistic. The existing negative PA
term partly cancels it, but delivered error worsens to +0.042810 from +0.023221
incumbent and +0.028826 matched. Support 197/118 and Flaherty, Shane Robinson
and Clint Robinson peers retain their poor or absent outcomes.

## Prospect opportunity remains a larger practical gap

Alvarez, row 35088, cutoff 2019-01-27, fold 2 prospect: 379 AA/AAA PA with
twenty HR and 92 K dominate older domestic work; 57 DSL PA are only 34.2 weighted.
Baseline −0.467743 plus residual +0.932254 = +0.464512, little changed from
matched +0.471745. Actual +5.647887 and 369 PA far exceed 72.2 PA. Opportunity
term −3.7083 exceeds hitting term −0.6235 at expected PA. Support 1,398/318 and
Sanchez, Singleton and Pederson peers remain; no favorable peer selection occurs.

Kurtz, row 57052, cutoff 2025-01-24, fold 2 prospect: only 35 A/15 AA PA with
four HR give baseline +0.238192 plus residual +0.393186 = +0.631378. Added MLB
effects are zero; old coefficient change lowers matched rate −0.022361. Actual
+5.150009 and 489 PA exceed 10.2 projected PA. The −5.6051 opportunity term
dominates the −0.0767 hitting term at that tiny workload. Support 2,538/561 and
Brooks Lee, DeLauter and Zunino peers remain; none justifies treating all such
players as immediate regulars. This test did not improve the opportunity model.

## Non arrivals are not observed zero talent

Maitan, row 31364, cutoff 2018-01-27, fold 4 prospect: 176 rookie PA with two
HR/49 K give baseline −1.132281 plus residual +0.839199 = −0.293081. All seven
MLB effects are zero. The 2.0 PA and +0.005137 value become a small positive
error when he has zero MLB PA. Neither hitting nor active opportunity is observed
for this target. Support 2,682/3 and absent Jhan Rodriguez, Starlin Balbuena and
Cesar Mejia peers stay. Do not use that absence to assign a batting rate of zero.

Tatis Jr., row 43296, cutoff 2022-03-18, fold 0 tracking: 546 MLB PA with 42 HR,
974.8 weighted MLB PA, give baseline +2.085676 plus residual +1.135085 =
+3.220761. Seven effects −0.042717 plus old change +0.002322 lower matched
value, improving its non-arrival squared error −0.351423. But +4.701195 value
at 553 projected PA remains a major error versus zero contribution and worsens
incumbent squared error +2.534841. Support 8/8 and Montero, Torres and Sanó
peers remain. Later absence cannot be recast as foreseeable zero hitting talent.

## Review decision

All seventeen inherited source/model walks and the new exact decomposition are
checked and retained, including unsuccessful peers. The matched seven-input
gain is not erased, the incumbent near-tie is not overstated, and cancellation
is no longer described as proof of improved ability. These walks do not isolate
the cause of the mature domestic loss or estimate which misses were avoidable
at the information date. The [result](hitter-restored-error-diagnosis-result.md)
states the aggregate evidence and one bounded next hypothesis. No new fitting,
forecast promotion or 2026 evaluation follows from this review automatically.
