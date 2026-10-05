# Actual player checks for freely learned hitting

2026-10-05. All seventeen fixed cases remain and three mechanically selected
cases are added. New cases are Cowser (largest delivered squared-error gain versus
incumbent), Acuña (largest positive delivered error) and Refsnyder (smallest absolute
delivered error among observed 200–399-PA players). Judge's rookie case remains
largest harm and false low. Selection explains behavior, not independent validation.

The unchanged [source counts and earlier fitted walks](hitter-mlb-events-restoration-player-review.md)
remain linked for all seventeen fixed players. Every new fit is replayed. The
new machine report includes the raw annual source counts, all adjustments and
prior shares, every fitted input/coefficient/effect, actual route/fold, full/active
joint support, fixed-fit removal probes and origin-only earlier comparison peers
for all twenty cases. No unsuccessful comparison is dropped.

## Exact model and forecast changes

Hitting rates are future MLB batting wins above league mean per 600 PA. The new
prediction equals fitted intercept plus all input effects, with zero offset.
Compared with matched residual prediction, the difference equals relearned
coefficient/intercept change minus the old baseline. Removing the baseline alone
is not the new fitted forecast. All equations verify. Sources and expected PA
are unchanged; value adds replacement, not defense or full WAR.

| Case and row | New intercept | All new feature effects | Relearned change | Removed baseline effect | Matched rate | New rate | Actual rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Judge 2016, 23934 | −0.490604 | +0.388788 | −0.549243 | +0.726057 | −0.278630 | −0.101816 | +5.329876 |
| Thames 2017, 27981 | −0.456904 | +1.224507 | +0.833956 | −3.149685 | +3.083333 | +0.767603 | +0.622421 |
| Maitan 2017, 31364 | −0.372481 | +0.526682 | −0.684998 | +1.132281 | −0.293081 | +0.154201 | Unobserved |
| Davis 2018, 32325 | −0.563930 | +2.935027 | +1.397781 | −1.428279 | +2.401596 | +2.371098 | −1.518480 |
| Wilkerson 2018, 32754 | −0.563930 | −0.668489 | −0.966658 | +1.112917 | −1.378678 | −1.232419 | −1.650306 |
| France 2018, 34339 | −0.429564 | +0.183219 | −1.180793 | +0.964989 | −0.030541 | −0.246345 | −1.059985 |
| Alvarez 2018, 35088 | −0.445687 | +0.656202 | −0.721739 | +0.467743 | +0.464512 | +0.210515 | +5.647887 |
| Nola 2021, 42235 | −0.751564 | +0.221434 | +0.313619 | −0.610894 | −0.232856 | −0.530130 | −0.924711 |
| Tatis 2021, 43296 | −0.574099 | +3.502827 | +1.793643 | −2.085676 | +3.220761 | +2.928728 | Unobserved |
| Suzuki 2022, 47765 | −0.613065 | +1.131980 | +0.543052 | −2.577305 | +2.553168 | +0.518915 | +1.996717 |
| Judge 2023, 50698 | −0.717845 | +4.668302 | +2.958787 | −2.756953 | +3.748623 | +3.950457 | +7.557649 |
| Misner 2024, 55509 | −0.716856 | −1.416909 | −0.795396 | +0.733207 | −2.071577 | −2.133766 | −2.025635 |
| Perdomo 2024, 55587 | −0.690306 | −0.059554 | −0.338245 | +0.264995 | −0.676609 | −0.749859 | +2.727891 |
| Kurtz 2024, 57052 | −0.630770 | +0.923018 | −0.100939 | −0.238192 | +0.631378 | +0.292248 | +5.150009 |
| Yoshida 2024, 57778 | −0.716856 | +1.414880 | +0.902035 | −1.596821 | +1.392809 | +0.698024 | −0.443798 |
| Lee 2024, 58061 | −0.690306 | +0.475349 | +0.192676 | −1.839976 | +1.432342 | −0.214957 | +0.463100 |
| Suzuki 2021 addition, 63309 | −0.391983 | −0.097065 | +0.117104 | −3.920524 | +3.314371 | −0.489049 | +1.174589 |
| Cowser 2024, 55900 | −0.690306 | +1.749120 | +0.063928 | −0.251675 | +1.246562 | +1.058815 | −1.344014 |
| Acuña 2023, 51153 | −0.717845 | +4.567849 | +2.403255 | −2.197207 | +3.643956 | +3.850004 | +0.723474 |
| Refsnyder 2022, 46682 | −0.693661 | +0.357145 | +0.507021 | −0.917360 | +0.073822 | −0.336516 | −0.232026 |

## Three new source to forecast walks

Cowser, row 55900, age 24, fold 1 tracking, cutoff 2025-01-24: latest MLB
561 PA, 24 HR/172 K/50 unintentional BB follow 77 MLB PA with zero HR/22 K
and 399 AAA PA with 17 HR/107 K in 2023. The 2022 A+/AA/AAA history remains,
giving 1,317.4 weighted all-source PA and 622.6 MLB PA. MLB K shrinks with
100 opportunities to 29.4215%, coordinate +0.642153; coefficient −0.321901
contributes −0.206710. Latest quality contributes +0.119966, pooled quality
+0.104268, age +0.336156 and upper-tail exit velocity +0.124369. These are
correlated learned terms, not isolated causal effects. Their full sum +1.749120
with intercept −0.690306 produces +1.058815, not the old baseline +0.251675.

At unchanged 476.9 versus 360 actual PA, new value 2.330982 is below matched
2.480216 and incumbent 2.698393, but actual is only 0.317827. Hitting error
+1.909932 and opportunity +0.103224 reinforce. Largest gain does not mean
a satisfactory forecast. Full/active support is 166/161; the actual earlier
training peers selected by past production/age/exposure/pedigree distance are
Schwarber 2017 (+0.827 next-year rate, 510 PA), Conforto 2017 (+1.314, 638)
and India 2021 (+0.274, 431). No peer was selected for that outcome.

Acuña Jr., row 51153, age 25, fold 3 tracking, cutoff 2024-01-26: latest
735 MLB PA, 41 HR/84 K/77 BB follow 533 PA with 15 HR/126 K and 360 PA with
24 HR/85 K; 25 AAA PA remain. Weighted MLB exposure is 1,377.4, all-source
1,397.4. K shrinks to 17.5173%, HR 4.7651%, BABIP 32.92% under the unchanged
100-opportunity denominators. Pooled quality adds +1.321844, latest quality
+0.727463, upper-tail EV +0.274036 and workload +0.297092. The full effects
+4.567849 with −0.717845 intercept produce +3.850004, versus matched +3.643956
and incumbent +3.826498. Good past evidence supports a strong rate, not a
guarantee of future availability or continued production.

New value 5.596138 at 588.3 PA versus 222 actual exceeds actual 0.955014.
Hitting error +3.065447 and opportunity +1.575677 reinforce. This is the new
false high, with delivered error +4.641124. We do not import later events as
preseason evidence or claim the absence was predictable. Support 125/125;
earlier peers Upton 2013 (+2.669, 641 PA), Suárez 2017 (+2.992, 606) and
Cabrera 2011 (+0.968, 616) retain their observed outcomes.

Refsnyder, row 46682, age 31, fold 3 tracking, cutoff 2023-01-26: MLB history
177/157/34 PA has 6/2/0 HR and 46/40/11 K. Latest AAA 182 PA with six HR,
seven AA PA with two HR and older AAA 80 PA with five HR remain. Weighted MLB
exposure is 323, all-source 576. K shrinks to 25.4374%, BABIP to 34.0353%
on 194.4 BIP opportunities. Age effect −0.481704, pooled quality +0.183500,
latest quality +0.149564 and launch-angle spread −0.139086 are among the
actual terms. Full effects +0.357145 plus intercept −0.693661 produce −0.336516
versus matched +0.073822, incumbent −0.165717 and actual −0.232026.

New value 0.668174 versus actual 0.666856 looks excellent at 260.0 expected
versus 243 actual PA, but hitting error −0.045275 cancels opportunity +0.046593.
Incumbent is closer in hitting. Support 214/129; earlier origin-selected peers
Barnes 2021 (+0.196, 212 PA), Nola 2021 (−0.925, 397) and Shaw 2021
(−15.284, nineteen PA) include a small-sample failure. The ordinary example
still cannot certify both submodels from a near-zero value error.

## Fixed overseas cases expose the tradeoff

Thames 27981, cutoff 2018-01-27, retains 551 MLB PA with 31 HR/163 K plus
older KBO power. Relearned change +0.833956 minus baseline +3.149685 lowers
matched +3.083333 to +0.767603, closer to +0.622421 actual. New pooled/latest
MLB quality effects +0.472998/+0.329365 preserve positive domestic evidence.
Foreign-removal probe falls only −0.264532 versus the earlier much larger
baseline dependence. Value becomes 1.935380 versus 1.143565 actual at 444.4/278
PA; both errors remain positive. Support 0/0 and Kang/Park/Hyun Soo Kim peers
are unchanged. Better than matched, still worse than incumbent value 1.641053.

Yoshida 57778, cutoff 2025-01-24, retains 421/580 MLB PA with 10/15 HR and
304.8 weighted NPB PA. New low-K effect +0.202127 and pooled quality +0.314136
sit against age −0.344033. Relearned +0.902035 minus +1.596821 baseline lowers
rate to +0.698024 versus −0.443798 actual. New value 2.041193 remains high
at 476.2/205 PA; hitting +0.906262 and opportunity +0.646372 reinforce. Support
0/0 and Aoki/Suzuki/Brosseau peers stay. The improved matched error is not a
resolved transfer or job forecast.

Suzuki 47765, cutoff 2023-01-26, retains 446 MLB PA with 14 HR/110 K plus
734.8 weighted NPB PA. Past HR contributes +0.199072 and pooled quality
+0.203502, but learned +0.543052 does not replace removed baseline +2.577305.
Rate falls to +0.518915 versus +1.996717 actual. New value 1.623392 versus
3.765501 actual at 406.3/583 PA loses much of matched improvement. Both errors
now miss low (−1.000647 hitting, −1.141461 opportunity). Support 2/1 and
Tsutsugo/Evans/Clark peers stay. Foreign-removal sensitivity −0.339363 does
not demonstrate a sufficient MLB equivalency.

Suzuki addition 63309, cutoff 2022-03-18, retains 1,659 NPB PA, 1,311.4
weighted, with no MLB source. Past HR adds +0.269568, but unknown/available
scout coordinates remain among negative terms. Learned +0.117104 barely offsets
removed +3.920524 baseline; rate becomes −0.489049 versus +1.174589 actual.
Value 0.443975 versus 2.270747 at 191.5/446 PA is much worse than matched.
Support 2/0 and absent Rosario/Nakajima/Meneses peers stay. There is no incumbent.
This sparse profile does not justify a foreign-specific selected model.

Lee 58061, cutoff 2025-01-24, retains 158 MLB PA with two HR/thirteen K and
685.8 weighted KBO PA. Low-K +0.291208 and age +0.224104 remain positive;
learned +0.192676 minus +1.839976 baseline drops rate to −0.214957 versus
+0.463100 actual. Hitting error −0.173636 is smaller in magnitude than matched
+0.248202, but no longer cancels opportunity −1.804626. Delivered error worsens
to −1.978261 at unchanged 153.6/617 PA. Support 0/0 and Kim/Hwang/Hyun Soo Kim
peers stay. The opposite hitting/value movement is not a source bug.

## Fixed MLB cases retain both gains and misses

Judge rookie 23934, cutoff 2017-01-28, retains 95 MLB PA with four HR/42 K
and 410 AAA PA with 19 HR/98 K. New pooled quality contributes −0.109300 and
age +0.304340. Relearned −0.549243 plus removed-negative-baseline +0.726057
raises rate to −0.101816, still below incumbent +0.264151 and +5.329876 actual.
New value 0.903689 at 309.9/678 PA improves matched but remains the largest
incumbent harm and false low. Hitting −2.805672 and opportunity −4.405401
reinforce. Support 6/5 and d'Arnaud/Alonso/Taylor peers stay.

Judge established 50698, cutoff 2024-01-26, retains 458/696/633 MLB PA and
37/62/39 HR. Pooled quality +1.697803, latest quality +0.462247 and past HR
+0.342559 preserve strong evidence. Learned +2.958787 minus +2.756953 baseline
raises rate to +3.950457, still far below +7.557649 actual. Value 5.188582
at 536.0/704 PA improves both anchors but still misses −5.858698. Support
19/19 and Stanton/Frazier/Alonso peers remain; not every superstar miss is fixed.

Davis 32325, cutoff 2019-01-27, retains 654/652/610 MLB PA and 48/43/42 HR.
Relearned +1.397781 nearly replaces removed +1.428279 baseline; +2.371098
remains far above −1.518480 actual. Value 4.027696 versus 0.292742 at 572.8/533
PA improves matched slightly, still worse than incumbent. Hitting +3.713107
dominates +0.021847 opportunity. Support 9/9 and Frazier/Dozier/Morales peers stay.

Perdomo 55587, cutoff 2025-01-24, retains 388/495/500 MLB PA with 3/6/5 HR.
Learned −0.338245 plus removed-negative-baseline +0.264995 lowers matched rate
to −0.749859 versus +2.727891 actual. Value 0.885237 at 472.6/720 PA still
improves incumbent but worsens matched; hitting −2.739325 and opportunity
−1.897378 reinforce. Support 60/55 and Thole/Brantley/Schafer peers stay.

Misner 55509, cutoff 2025-01-24, retains ten K in fifteen MLB PA plus substantial
AAA work. Upper-tail/mean EV effects −0.478886/−0.434128 contribute to the
new pessimism. Learned −0.795396 plus removed-negative-baseline +0.733207
lowers rate to −2.133766, farther from actual −2.025635 than matched −2.071577.
Value −0.036634 moves closer to actual −0.054941 at 84.5/217 PA because hitting
−0.015233 cancels opportunity +0.033540. Support 641/422 and Harrison/Deichmann/
Tucker peers stay. This matched value gain is not improved hitting accuracy.

## Ordinary and prospect cases do not disappear

Wilkerson 32754, cutoff 2019-01-27, retains 49 MLB PA, sixteen K/no HR and
mixed minor history. New rate −1.232419 is farther from −1.650306 actual than
matched, yet value 0.112384 nearly matches 0.118958 at 109.5/361 PA. Hitting
+0.076289 cancels opportunity −0.082864. Support 341/209 and Martinez/Mejia/
Perkins peers stay; learned −0.966658 plus +1.112917 removed-baseline effect
explains the optimistic movement.

France 34339, cutoff 2019-01-27, retains 479 AA/110 AAA PA with 17/5 HR and
25/2 HBP, no MLB. Learned −1.180793 plus +0.964989 baseline removal lowers
rate to −0.246345, closer to −1.059985 actual. Value 0.232266 at 87.0/201 PA
is less exact than matched 0.263560 versus 0.263992 actual, because hitting
+0.117989 now offsets less of −0.149716 opportunity. Support 1,444/326 and
absent Bandy/Puello/Pohl peers remain.

Nola 42235, cutoff 2022-03-18, retains 194/184/267 MLB PA, 2/7/10 HR,
including actual short 2020. Learned +0.313619 minus +0.610894 baseline lowers
rate to −0.530130, closer to −0.924711 actual. Value 0.553230 at 245.9/397 PA
is worse than matched 0.675044 versus 0.632234 actual as hitting +0.161687
offsets less of −0.240691 opportunity. Support 197/118 and Flaherty/Robinson/
Robinson peers stay. Rate and delivered accuracy remain different questions.

Alvarez 35088, cutoff 2019-01-27, retains 379 AA/AAA PA with twenty HR/92 K
and only 34.2 weighted old DSL PA. Learned −0.721739 plus +0.467743 removed
baseline lowers rate to +0.210515 versus +5.647887 actual. Value 0.247623 at
72.2/369 PA worsens both anchors; hitting −0.654065 plus opportunity −3.708296
miss low. Support 1,398/318 and Sanchez/Singleton/Pederson peers stay. No new
opportunity estimate was learned and no DSL-heavy explanation is invented.

Kurtz 57052, cutoff 2025-01-24, retains 35 A/15 AA PA with four HR, no MLB.
Learned −0.100939 minus +0.238192 baseline lowers rate to +0.292248 versus
+5.150009 actual. Value 0.036764 at 10.2/489 PA remains far below 5.724344;
opportunity −5.605128 dwarfs hitting −0.082452 at expected PA. Support 2,538/561
and Brooks Lee/DeLauter/Zunino peers remain. A tiny hitting term does not mean
his conditional talent was predicted well.

Maitan 31364, cutoff 2018-01-27, retains 176 rookie PA with two HR/49 K,
no MLB. Learned −0.684998 plus +1.132281 baseline removal raises rate to
+0.154201 and value to 0.006617 at 2.0 expected PA. Actual contribution is zero,
not an observed zero hitting rate. Support 2,682/3 and absent Rodriguez/Balbuena/
Mejia peers stay; no active error decomposition is assigned.

Tatis Jr. 43296, cutoff 2022-03-18, retains 546 MLB PA with 42 HR and 974.8
weighted MLB PA. Learned +1.793643 minus +2.085676 baseline lowers rate to
+2.928728. Value 4.432050 at 553.0 PA is closer to incumbent 4.423391 but still
a major error versus zero contribution. Conditional hitting is unobserved for
that target. Support 8/8 and Montero/Torres/Sanó peers stay; later absence is
not reclassified as a forecast-time zero-talent signal.

## Decision after the player checks

Twenty full source/model walks are complete, including all prior cases and the
three new ones with their actual earlier peers. Removing the imposed baseline
does not uniformly improve established or foreign players, and gives up prospect
signal. It helps some hitting estimates while worsening value through lost
compensation, and vice versa. No case warrants a fitted subgroup switch or
another guessed offset weight. The [aggregate result](hitter-absolute-rate-result.md)
keeps all origins, cohorts, totals, benchmarks and uncertainty. Retain incumbent;
the frozen forecast, existing explorer and completed 2026 evaluation are unchanged.
