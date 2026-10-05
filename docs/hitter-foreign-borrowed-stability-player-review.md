# Player review of the borrowed overseas hitting translation

2026-10-04. This review compares the repaired affine and borrowed-stability
foreign-only components. It does not compare whole hitting models or forecast
MLB jobs, PA, defense or WAR. All fourteen cases fixed before fitting are kept,
including an absent profile and a non-arrival. Outcome-selected cases are
diagnostics, not independent confirmation. No parameter is adjusted from them.

## Inputs and calculation used for every case

The source is each player's actual three-year NPB/KBO history, with 5/4/3
recency weights multiplied by observed PA. Half-event smoothing makes the
eight mutually exclusive probabilities well-defined. Each source is compared
with the complete same-season league distribution after identified held folds
are removed, not just overseas players who eventually reached MLB. Missing
other-league observations do not imply unemployment or no talent.

For each outcome, source coordinate x is its centered log-ratio probability
minus the similarly pooled league reference. Domestic calibration supplies a
and b; earlier overseas movers supply offset d. The output is softmax of
origin MLB reference log probabilities plus a + d + b*x across all eight
outcomes. Thus a K probability depends on normalization of the full vector;
b is not a multiplier on raw K percent. All histories are cutoff-bounded and
the focal player's fold is excluded from estimation and identified references.

Private `review-supplement.json` records raw annual counts, actual MLB histories,
all a/b/d/reference/source coordinates, reconstructed probabilities, actual
support intersections, range warnings and peers. The source histories and
outcome-blind peers from the preceding fourteen walks are retained exactly in
`reviewed-cases.json`. New score-selected comparisons choose the three nearest
same-origin/dominant-league profiles using age, exposure, K and HR before
consulting outcomes. These comparisons do not match MLB employment or establish
exchangeable job probabilities; their non-arrivals therefore matter.

All profiled cases below are within the marginal domestic coordinate ranges.
That is NOT proof of adequate joint age/contact/power support or foreign league
equivalence. Foreign mover support is sparse even with hundreds of domestic
people. Domestic totals below count distinct training people, not repeated rows.

## Fixed cases and observed rates

Percentages are per PA. Old means repaired affine; new means borrowed stability.
Source PA is the unweighted three-year foreign total; actual PA is next-year MLB.
The private source trace retains per-season exposure instead of disguising it
as a complete three-year season. Domestic and mover counts are for each actual
case's historical fold, not the full modern calibration sample.

| Player and origin | MLBAM | Source PA | Domestic people | Relevant movers | Next MLB PA | K old/new/actual percent | HR old/new/actual percent |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Ohtani 2017 | 660271 | 732 | 775 | NPB 11 | 367 | 21.84 / 26.62 / 27.79 | 2.82 / 3.40 / 5.99 |
| Suzuki 2021 | 673548 | 1,659 | 907 | NPB 13 | 446 | 21.62 / 18.32 / 24.66 | 2.81 / 3.71 / 3.14 |
| Yoshida 2022 | 807799 | 1,455 | 1,031 | NPB 13 | 580 | 17.19 / 11.16 / 13.97 | 2.55 / 2.94 / 2.59 |
| Fukudome 2007 | 493120 | No sealed profile | — | — | 590 | Not estimated | Not estimated |
| Tsutsugo 2019 | 660294 | 1,738 | 887 | NPB 12 | 185 | 22.53 / 23.49 / 27.03 | 3.40 / 3.95 / 4.32 |
| Tanaka 2012 | 547887 | 1,387 | 511 | NPB 5 | 34 | 16.84 / 12.30 / 8.82 | 1.37 / 0.85 / 0.00 |
| Jung Hoo Lee 2023 | 808982 | 1,558 | 1,115 | KBO 7 | 158 | 21.28 / 12.95 / 8.23 | 2.86 / 2.61 / 1.27 |
| Ha-Seong Kim 2020 | 673490 | 1,823 | 887 | KBO 4 | 298 | 23.79 / 20.36 / 23.83 | 3.85 / 3.55 / 2.68 |
| Hyeseong Kim 2024 | 808975 | 1,754 | 1,200 | KBO 9 | 170 | 20.82 / 18.70 / 30.59 | 2.04 / 1.40 / 1.76 |
| Park 2015 | 666560 | 1,749 | 654 | KBO 1 | 244 | 21.32 / 24.44 / 32.79 | 3.34 / 5.05 / 4.92 |
| Thames 2015 | 519346 | 1,109 | 656 | KBO 1 | 0 | 20.00 / 19.48 / Unobserved | 3.04 / 4.47 / Unobserved |
| Thames 2016 | 519346 | 1,638 | 707 | KBO 3 | 551 | 21.75 / 22.46 / 29.58 | 3.53 / 4.44 / 5.63 |
| Jung Hoo Lee 2024 | 808982 | 1,014 | 1,185 | KBO 8 | 617 | 20.93 / 12.26 / 11.51 | 2.86 / 2.83 / 1.30 |
| Ha-Seong Kim 2022 | 673490 | 622 | 1,017 | KBO 4 | 626 | 22.71 / 18.59 / 19.81 | 3.43 / 3.39 / 2.72 |

### Ohtani and Suzuki

Ohtani's 2015/2016/2017 source has 119/382/231 PA, 43/98/63 K and
5/22/8 HR. The recency pool gives 27.25% K and 4.83% HR before translation.
Borrowed K persistence is 0.647 and HR persistence 0.702. The larger source
contrast now survives more strongly: debut contact moves closer, but HR still
misses by 2.60 percentage points. His two-way hint is retained, not converted
to exclusive hitter eligibility. There is no original pre-arrival forecast.
His three retained source peers all have zero next-year MLB PA; similar batting
production cannot by itself imply his MLB employment or pitching value.

Suzuki's 2019/2020/2021 source has 612/514/533 PA, 81/73/88 K and
28/25/38 HR. More persistence of his low-K/high-power Japanese profile moves
K below his actual MLB debut and HR above it. Both K and HR absolute errors
worsen. The full vector mechanism—not an accidentally reversed comparison—
produces this tradeoff. The same three origin-known Japanese power peers have
zero following-year MLB PA. Overseas skill preservation is not guaranteed to
improve MLB adaptation prediction or opportunity.

### Yoshida and Fukudome

Yoshida's 2020/2021/2022 source has 492/455/508 PA, 29/26/41 K and
14/21/21 HR. Strong low-K evidence receives more persistence; debut K improves
slightly in absolute error but HR worsens from a very close old match. His
three source peers do not enter MLB the next year. The better contact estimate
does not establish improved total hitting value, job probability or defense.

Fukudome remains the fixed 2007-origin coverage control. He has reviewed raw
NPB history in the preceding source work and 590 observed debut MLB PA, but
lies outside this sealed 2011+ input population. No model, foreign translation,
zero forecast or false training-support claim is manufactured. His three
origin-known comparisons are preserved in the prior source trace. This is an
explicit scope gap, not a successful forecast or evidence of no talent.

### Tsutsugo and Tanaka

Tsutsugo's 2017/2018/2019 source has 601/580/557 PA, 115/107/141 K and
28/38/29 HR. The new output moves both K and HR closer to the observed debut.
The target is shortened 2020: 185 actual PA, not a normal-year workload test.
It is retained as a descriptive fixed control, outside the primary mover
calibration target. All three source peers have zero MLB PA in that target.

Tanaka's 2010/2011/2012 source has 662/220/505 PA, 66/21/36 K and
5/1/3 HR. Better preservation of low K/low power moves both closer, but his
34 MLB PA cannot certify the latent skill. Only five NPB movers estimate the
foreign adjustment. One retained source peer, Aoki, records 674 following-year
MLB PA while two others record none. A plausible offensive profile can support
different workloads, which this component does not estimate.

### Lee and the two Kims

Lee's 2021/2022/2023 KBO source has 544/627/387 PA, 37/32/23 K and
7/23/6 HR. His smoothed recency pool has 5.88% K. Domestic K persistence
0.688 and the seven-mover foreign offset produce 12.95%, replacing the overly
compressed 21.28%. It is closer to observed 8.23%, but power remains high.
All three retained source peers have zero following-year MLB PA. A later
injury cannot become a forecast-time explanatory variable.

Ha-Seong's 2018/2019/2020 source has 576/625/622 PA, 81/80/68 K and
20/19/30 HR. The real overseas 2020 history remains valid before normal MLB
2021; it is not a canceled MiLB zero. With only four Korean movers, stronger
source persistence makes debut contact worse even as HR gets closer. His source
peers—including Lee at that origin—do not enter MLB the next year. Do not turn
this contact miss into a universal Korean-player penalty.

Hyeseong's 2022/2023/2024 source has 566/621/567 PA, 83/77/62 K and
4/7/11 HR. Despite a substantial low-K history, observed first MLB K is
30.59% over 170 PA. Preserving his low-K signal moves farther from that result;
HR absolute error also grows. His current unchanged PA forecast is only
0.3615, a separate missing-history/context problem not repaired by these rates.
The three source peers have zero next-year MLB PA. Neither those outcomes nor
this single season establish that all similar overseas contact hitters fail.

### Park and Thames

Park's 2013/2014/2015 source has 556/571/622 PA, 96/142/161 K and
37/52/53 HR. Power now translates to 5.05%, close to observed 4.92%; K remains
well below observed 32.79%. Only one Korean mover supports the adjustment in
his held fold. His source peers, including Thames, have zero following-year
MLB PA. The power match is useful descriptive evidence but thin validation.

Thames at origin 2015 has 514/595 PA, 99/91 K and 37/47 HR in 2014/2015.
No 2013 KBO season is fabricated. The new component preserves high power,
but there is no observed 2016 MLB hitting rate because MLB PA is zero.
The source peer Kang has 370 following-year MLB PA, while two others have zero.
These controls prevent a high hypothetical rate from implying an MLB job.

At origin 2016, Thames adds 529 PA, 103 K and 40 HR. New K and HR both move
closer to his 551-PA MLB return, yet remain low. His saved expected PA stays
20.78; this experiment cannot repair that shortfall. Retained same-origin peers
include one 57-PA MLB season and two non-arrivals, supporting explicit job
uncertainty rather than automatic opportunity from strong foreign power.

### Later MLB evidence for Lee and Ha-Seong

Lee at origin 2024 retains older 2022/2023 KBO history, but also has 158 recent
MLB PA with 13 K and two HR. The foreign-only K output improves considerably
against 2025, while HR remains too high. His retained comparisons include
Hyeseong's 170-PA MLB debut and two non-arrivals. The complete model must receive
Lee's actual MLB evidence; it must not replace it with this foreign-only result.

Ha-Seong at origin 2022 retains only the older 622-PA KBO season in the three-year
window. Meanwhile, MLB 2021/2022 supplies 298/582 PA, 71/100 K and 8/11 HR.
The new foreign-only estimates improve against 2023 but omit those 880 MLB PA
by design. His peers include Suzuki's 583-PA season and two non-arrivals.
A component diagnostic cannot authorize prioritizing older foreign history
over the more direct current MLB evidence as that evidence grows.

## Score selected gains and misses

### James Adduci at origin 2018

MLBAM 451192 is both the largest gain and largest K false low. His only recent
foreign input is 2016 KBO: 272 PA, 59 K, seven HR, 18 BB including one IBB.
It lies at lag two; 2017/2018 has 93/185 actual MLB PA with 27/45 K and one/three
HR, intentionally unused by this foreign component. Four Korean movers and
825 domestic people calibrate the case. K persistence 0.661 produces 28.13%
versus old 25.65%; HR becomes 2.15% versus old 2.93%. Three actual K in five
target PA means observed 60% K and log-loss improvement -0.061792. This is
small-sample outcome noise, not proof of a discovered 60%-K player or meaningful
full-model benefit. The three source-selected peers (457760, 611177, 476192)
all have zero target MLB PA. The aggregate PA-weighted and 100-PA diagnostic
are necessary context and remain favorable without treating this case as truth.

### Henry Ramos at origin 2022

MLBAM 592656 is the largest log-loss harm. KBO 2022 supplies 80 PA, 18 K,
three HR and four BB. MLB 2021 already supplies 55 PA, 12 K and one HR, outside
this component. The profile has six Korean movers and 1,031 domestic people;
K/HR persistence is 0.658/0.719. K moves 24.26% to 26.83% versus 24.42%
observed in 86 PA; UBB falls 7.90% to 5.94% versus 12.79% observed. HR moves
2.86% to 3.08% against zero. The adverse vector explains +0.020876 loss, not
an unknown model-library effect. Eighty foreign PA plus a few movers is weak
support for a fine skill adjustment. Peers 596825, 594953 and 541650 all have
zero target MLB PA; their lack of jobs does not validate Ramos's rate.

### Yuli Gurriel at origin 2016

MLBAM 493329 is the largest K false high. The foreign window contains only
2014 NPB: 258 PA, 40 K, 11 HR and 15 BB. The Cuba history is uncollected, not
zero. MLB 2016 already has 137 PA, 12 K and three HR. With 707 domestic people
and eleven NPB movers, K/HR persistence 0.673/0.734 produces K 17.68% versus
old 18.64% and actual 10.99%; HR 2.94% versus old 2.26% and actual 3.19%.
Both improve but the contact miss remains. The old overseas season alone is
not his complete skill history. His selected peers (467070, 461882, 518755)
all have zero target MLB PA. Using the available low-K MLB debut in the complete
model is warranted; selecting a special Cuban override from his outcome is not.

### Masataka Yoshida at origin 2024

MLBAM 807799 is the smallest absolute change in overall log loss. The older
foreign window contains 2022 NPB: 508 PA, 41 K, 21 HR, 80 BB including 18 IBB.
MLB 2023/2024 has 580/421 PA, 81/52 K, 15/10 HR and 34/27 UBB. With 1,187
domestic people and thirteen NPB movers, the foreign K estimate changes from
16.61% to 12.46%, close to observed 11.71% in 205 PA. But UBB increases from
9.02% to 10.57% against 4.88%; HR increases from 2.80% to 3.29% against 1.95%.
The good K change is largely offset elsewhere, leaving -0.001065 overall loss.
His peers (641914, 676950, 641741) have zero target MLB PA. The complete model
must not erase his 1,001 more recent MLB PA to chase the foreign K success.

## Ordinary and unresolved source controls

The source-rule-selected 2024 Aoki (493114) and Choo (425783) remain outside
the sealed input population with no invented profile or job. Their source
129 and 302 PA are genuine production, not zero talent. The unresolved NPB
published ID 01305131 remains unjoined with 125 PA; future MLB participation
is unknown, not a scored zero. Their exact previous records remain unchanged.

## Review conclusion

The gain survives larger-sample diagnostics, but the foreign portability
assumption has visible counterexamples and substantial selection/park limits.
Preserve raw counts/exposure and actual intervening MLB evidence. Retain this
candidate for one whole-model comparison after the ordered-status/addition
repair. No deployment or full-player-value gain is established by this review.
The same 253 source forecasts, 225 unobserved hitting outcomes and original
full-model forecasts remain untouched. Protected 2026 is unchanged.
