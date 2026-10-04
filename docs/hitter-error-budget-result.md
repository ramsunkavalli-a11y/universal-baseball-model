# Where the hitter forecast errors come from

2026-10-04. The current model has different problems in different populations.
For public MLB players, variation in workload after appearing accounts for most
playing-time squared error. For upper-minors prospects, the total PA shortfall
mostly reflects where arrival probability is allocated. Neither is fixed by a
universal playing-time boost. Almost correct total contributions sometimes hide
large errors in both workload and hitting.

## What was measured

This [locked diagnostic](hitter-error-budget-contract.md) changes no forecast
and fits no model. It retains all 30,506 historical rows, seven origins, exits
and non-arrivals. Public matches retain 2,627 rows across targets 2022–25. Dated
history and following-preseason ranking qualifications remain; these are not
fully refreshed Opening Day forecasts. Protected 2026 remains closed.

All event-derived PA, common-origin rates and contributions independently
recompose. Every PA/value error identity and each loss allocation recompose;
36 saved heads replay for twelve actual walks. Rate input transformations and
every linear contribution are preserved. Unit tests check cancellation, unequal
year sizes, non-arrivals with undefined production and signed yield. These are
execution checks, not new predictive validation or proof of unavoidable error.

For PA, participation error is (p-a)c and active-workload error is a(c-y), where
p is appearance probability, c conditional PA, a actual appearance and y actual
PA. For contribution, multiply those two terms by forecast yield and add actual
PA times forecast-minus-realized yield. Non-arrivals have no observed production
or conditional workload error. No imaginary zero batting talent is assigned.
Contribution here means common-origin fixed-event batting plus replacement,
not official WAR, defense, running, club control or trade value.

Squared error contains component squares and cross products. The following
allocations are component times total error, averaged with equal target-year
weight; they sum exactly to total MSE. They depend on the stated ordering and
may be negative. They are not independent causal percentages or the amount a
new model can remove. Realized production includes sampling variation and
unforeseeable change, not just missed predictable talent.

| Population | PA MSE participation | PA MSE active workload | Contribution MSE participation | Contribution MSE workload | Contribution MSE production |
| --- | ---: | ---: | ---: | ---: | ---: |
| All | 737.822 | 2922.319 | .006037 | .048595 | .150925 |
| Public matches | 3014.474 | 16120.673 | .029849 | .264839 | .829982 |
| Upper minors never debuted | 1035.414 | 2003.544 | .007378 | .022782 | .067704 |
| Lower minors never debuted | 29.177 | 34.286 | .000219 | .000501 | .001133 |

The public PA RMSE remains 138.330 versus Steamer 135.379 and MAE 106.411
versus 92.083. The benchmark is unchanged. We cannot decompose Steamer into
these heads because its corresponding probabilities and conditional workloads
are not supplied. Every case below is diagnostic, not an improvement claim.

## Bias is different from individual squared error

Upper-never-debut expected PA are 74,239 versus 92,891 actual. Participation
allocation accounts for -17,147 of that signed total error and active workload
-1,504. This does not mean conditional workloads are individually accurate:
they supply the larger squared-error allocation above. Their over- and
underestimates largely cancel in the total.

Public expected PA are 649,255 versus 660,776. Participation allocation is
-13,679 and active workload +2,158. Again, mean bias and squared-error sources
differ. A global conditional boost targets neither diagnosis well. Current
listed MLB hitters have 1,001,415 expected PA versus 1,037,360; listing=0 current
hitters instead have 128,282 versus 119,496, with opposite component offsets.
Listing is the qualified returned historical proxy, not a certified contract
or employment guarantee. Solano does not justify boosting every unlisted veteran.

Upper-minors forecasts in the .10–.50 probability band expect 219 arrivals
versus 291 actual and 23,519 PA versus 36,217. In the .80–1 band, expected
arrivals are 58 versus 53 and PA 13,573 versus 12,362. Lower-minors forecasts
below .01 expect 45 arrivals versus ten actual, while their .01–.10 band
expects twenty versus 25. These are pooled descriptive bins, not a calibration
fit, independent causal evidence or permission for an across-the-board boost.
Every origin, PA band, signed bias, cross-product matrix and cancellation score
is saved in [the summaries](../reports/model-evidence/hitter-error-budget/scores.json).

## Actual player traces

The [case archive](../reports/model-evidence/hitter-error-budget/cases.json)
contains raw three-season level histories, actual target MLB counts, all 251
opportunity and 199 batting inputs, saved paths, scaled linear terms, models,
support and four outcome-blind peers. A broad support count is not a count of
close talent, injury or employment analogues. Earlier uncertainty/location
walks supply additional provenance; their forecasts remain exact.

**Aaron Judge 2024, row 54849.** Three MLB seasons contain 696/458/704 PA and
62/37/58 HR. Listing=1, 158 games and current production yield 99.07% appearance,
535.74 conditional PA and 530.75 expected PA. The batting head independently
replays at 4.534 custom wins/600; pooled quality contributes +2.683 and current
quality +1.300 among its linear terms, with all other terms retained. Actual
679 PA and rate 6.427 produce 9.393 contribution versus 5.668 forecast.
Participation/workload/production errors are -.053/-1.530/-2.142: no compensating
error. Ohtani/Ozuna/Marte/Harper are broad controls; rate-profile support eighty
does not prove adequate superstar-tail learning. A better arrival classifier
alone would change little here.

**Nick Kurtz 2024, row 57052.** Fifty A/AA PA, four HR, twelve walks and ten K are
received alongside draft and scouting evidence. Probability 6.06% and conditional
168.16 yield 10.18 expected PA. Batting -.063 replays, with age +.619 and draft
+.165 among terms, versus realized 5.289 over 489 PA. Contribution .031 versus
5.838 splits -.477/-.968/-4.362. The large realized production term is not proof
that a future star was certain, nor an excuse for near-zero readiness. The rate
support count 1,005 is broad; the earlier refined workload intersection was
empty. Ariza/Avila/Chevalier/Quero all non-arrive but are weak elite-talent peers.

**Wyatt Langford 2023, row 53164.** His 200 professional PA include eighty at AA/AAA,
ten HR, 36 walks and 34 K. Scouting is present; 59.91% times 358.74 yields
214.92 expected PA. Batting .688 replays against realized .077 over 557 PA.
Value .912 versus 1.796 contains -.610 participation, -.841 workload and +.567
optimistic production. That hitting error partly masks the PA shortfall. Crews
received 132 PA and DeLauter/Montgomery/Teel zero. Broad rate support 965 and
empty refined workload support are different facts, not proof of plentiful
elite-entry examples. Increasing workload alone is not a complete hitting fix.

**Bryan Reynolds 2018, row 34859.** The source has 383 AA PA after 541 A-plus PA,
with seven HR, forty walks and 73 K in the current season. Model probability
15.64% times conditional 81.02 yields 12.67 PA. Rate -.430 receives separate
minor histories but misses realized 3.312; value .030 versus 4.696 splits
-.162/-1.099/-3.406. All errors reinforce. Rate support 553 is a broad
intersection; Milone/Bishop/Hendrix/Lund actual 0/60/0/0 cannot validate this
forecast for a productive AA hitter. Both opportunity and talent translation
remain visible, not explained away by a coarse non-arrival peer group.

**Donovan Solano 2022, row 46330.** His source has 203 short-2020 PA, then 344 and
304, with four HR, eighteen walks and 61 K most recently. Listing=0 contributes
negatively to probability, but does not certify absence. Probability 42.25%
and conditional 304.30 yield 128.57 expected PA versus 450. Batting -.117
contains age -.708, current work +.473 and position +.302 among terms; realized
rate is 1.569. Value .377 versus 2.585 splits -.516/-.428/-1.265. All are too
low in this realized season. Brantley/Moustakas/Ruf/La Stella have varied returns;
fixes must retain their low-workload cases, not only this successful veteran.

**Joey Votto 2023, row 50568.** MLB PA fall 533 to 376 to 242. Age 39, listing=0
and left-truncated career history enter the heads. Probability 43.33% times
conditional 328.33 gives 142.25 PA; batting -.083 yields .421 contribution.
Actual zero supplies only +.421 participation-allocation error. No realized
batting or active-workload comparison exists. Gurriel/Donaldson/Longoria/Cabrera
actual 65/0/0/0 caution against treating all older hitters as certain exits.
The previous median gain did not improve expected player value.

**Brandon Belt 2023, row 50571.** Histories contain 381/298/404 MLB PA and 29/8/19 HR.
Age 35, listing=0 and positive production produce 64.63% appearance, 377.77
conditional and 244.16 expected PA. Batting .686 replays with pooled quality
+.717 and age -.890 among terms, yielding 1.035 contribution. Actual non-return
makes the whole error participation allocation; his hypothetical batting rate
is unobserved. Martinez/Blackmon/McCutchen/Canha all return substantially. Keep
this as a reasonable projection that missed unusual employment, not a universal
aging penalty or hidden talent collapse.

**Kevin Maitan 2017, row 31364.** Age seventeen, 176 rookie PA, two HR, ten walks and
49 K enter the inputs with shortstop/scouting evidence. Probability 1.52% and
conditional 130.37 give 1.99 expected PA. Batting -.206 replays with age and
negative position/intercept offsets; it is not observed MLB talent. Actual zero
yields only .005 contribution-allocation error. Garcia/Sosa/De La Torre/Nova
also have zero next-year PA. Rate support 489 and empty refined workload support
cannot certify eventual teenage success. The tiny immediate error says little
about long-term prospect valuation.

**Chris Davis 2017, row 27537.** This largest false high has 670/665/524 PA,
47/38/26 HR and worsening K rate in its actual inputs. Participation 97.51%
and conditional 515.52 give 502.67 PA versus 522, a close workload forecast.
Rate 1.082 contains positive pooled quality and historical workload contributions,
versus realized -4.102. Contribution 2.452 versus -1.963 splits -.063/-.032/+4.510.
The issue is production, not PA. Moreland/Valencia/Duda/Alonso do not have the
same extreme collapse. Decline evidence existed, but this diagnostic does not
establish how much collapse could be predicted or justify a player-specific rule.

**Aaron Judge 2016, row 23934.** The largest false low has 410 AAA PA with nineteen
HR, 47 walks and 98 K, then 95 MLB PA with four HR, nine walks and 42 K.
Those separate levels enter the rate model. Participation 92.50% and conditional
335.05 give 309.92 PA versus 678; batting -.040 versus realized 5.557 leaves
contribution .936 versus 8.372. Errors -.076/-1.036/-6.325 reinforce. The
extraordinary rookie season was not guaranteed by his AAA record. Moya/Waldrop/
Renfroe/Brito have mixed later activity; broad rate support 239 is not exact
star-contact support. Both weak workload and uncertain talent translation remain.

**José Bautista 2016, row 22833.** The largest cancellation has 673/666/517 PA and
35/40/22 HR. Age 35 and listing=0 lead to 53.70% appearance and conditional
503.68, or 270.48 PA versus 686. Rate 2.277 replays with pooled quality +1.271
and age -.741 among terms, versus realized -.995. Forecast contribution 1.861
versus .979 looks relatively close because -1.605 participation and -1.254
workload offset +3.741 production; absolute cancellation is 5.718. Granderson/
Pence/Smith/Zobrist have different realized declines. This is not a sound
conservative model that correctly foresaw decline: it got both components wrong.

**Ben Rortvedt 2023, row 51344.** The closest ordinary active value case fails the
component smell test. MLB PA are 98/0/79 with recent AAA exposure; current MLB
has two HR, eleven walks and nineteen K. Listing=1 and 87.33% participation
still give only 94.22 conditional and 82.28 expected PA versus 328. Rate -1.102
contains pooled quality -.370 and catcher position -.255 among terms, versus
realized -1.669. Value .103664 versus .102959 is almost exact only because
-.015/-.295/+.310 cancel. Herrera/Pinto/Amaya/Viloria actual 114/49/363/0
show role variation. Keep this inconvenient ordinary-by-value selection, rather
than replacing it with a flattering case. Final-value closeness alone is unsafe.

## Decision and the next bounded comparison

All twelve player reviews are complete. Retain this accounting, not a changed
forecast. The source and calculations passed; important errors remain, and
the full goal is active. In particular, large production allocations cannot
be read as wholly fixable talent-model defects: the current qualified public
rate comparison is already competitive and future seasons are genuinely noisy.

Prior specialized entrant training did not improve conditional workload;
employment flags and last-season team record did not repair public forecasts.
The available-season representation helped some arrival probabilities but not
whole value enough to promote. Direct contribution/event-count means also lost.
None justifies a global prospect or veteran boost.

Next make one matched positive-workload capacity comparison on current inputs:
keep appearance and batting fixed; compare the saved shallow conditional head
with deeper histogram trees and matched-capacity LightGBM conditional means.
The older role study used 77 inputs, a different multi-year panel and no complete
held-player exclusion; the earlier direct-PA comparison changed an unconditional
target. Neither settles this particular 251-input conditional-head question.
This targets the large public active-workload squared error without changing
the mean into a median, importing new flags or claiming unsupported prospect
certainty. Lock settings, whole-player chronology and all-player scoring before
fitting; retain clipping, profile gaps, cohort totals and actual player harms.
If it provides no coherent improvement, do not tune around the exposed cases.

Evidence: [probability bins](../reports/model-evidence/hitter-error-budget/probability-bins.json),
[full cases](../reports/model-evidence/hitter-error-budget/cases.json),
[verification](../reports/model-evidence/hitter-error-budget/verification.json)
and [completed review](../reports/model-evidence/hitter-error-budget/final-report.json).
