# Player review of the playing time uncertainty test

2026-10-03. Fourteen actual forecasts were reviewed from source counts through
saved point models, nested spread estimates and full probability distributions
to next-calendar-year MLB PA. The review is complete; that does not mean the
method is calibrated for every player or ready for deployment. The principal
finding is that a sensible positive-workload spread helps some forecasts, but
cannot repair an incorrect chance of arrival or return.

## What was held fixed and how cases were chosen

The current candidate supplies p, the chance of any MLB PA, and c, PA conditional
on appearing. Expected PA remains p times c. Hitting and expected offense do not
change. The new distribution keeps exactly 1-p probability at zero; if active,
PA is 1 plus a beta-binomial count with 799 trials, beta mean (c-1)/799 and
concentration k. The narrow reference substitutes a binomial with the same p
and c. The older forest has different features, means and participation odds;
it is a useful empirical reference but not a controlled spread-only comparison.

Eight fixed cases preceded fitting. Outcome-selected cases add the largest
quantile-score gain and harm against each reference, the largest positive and
negative mean errors, and an ordinary active case nearest its mean. Repeated
selections are retained once, with all reasons in the evidence. Names and
identities below cannot be swapped out because the example is inconvenient.

The saved fits use their actual coming-season information dates, not an invented
common December cutoff. Statistics end with the origin season; preseason rank
release dates vary. All nested spread labels were mature at the outer cutoff;
each nested predictor had its own earlier cutoff and excluded both outer and
inner held-player groups. There are 95 nested contexts but only 50 distinct
saved heads: identical memberships permit exact reuse. All 50 were replayed,
all 35 concentrations recomputed, and both point heads for each case replayed.
Forty-two case quantiles were independently checked with scalar inverse CDFs.

The uncertainty model does not add park/opponent corrections, new medical facts,
foreign batting histories, fielding or running to the current point models.
Existing rates, separate level counts, shrinkage, recency and role inputs remain
exactly as in the current candidate. All 251 actual inputs and saved path
contributions are retained per case, not inferred from the player's name.

## Identities and spread estimation

Rows identify the existing evaluation population. Calibration people are
distinct earlier active players, not independent repeated seasons. Profile
people are earlier active matches in the predefined refined profile; large
counts do not establish equivalent star talent or medical circumstances.

| Player and origin | Row | Fold | Information date | k | Calibration rows / people | Profile people |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| Nick Kurtz 2024 | 57052 | 2 | 2025-01-24 | 5.6904 | 400 / 186 | 0 |
| Wyatt Langford 2023 | 53164 | 4 | 2024-01-26 | 5.5132 | 378 / 176 | 0 |
| Pete Alonso 2018 | 33263 | 1 | 2019-01-27 | 5.2647 | 411 / 180 | 5 |
| Aaron Judge 2016 | 23934 | 3 | 2017-01-28 | 4.5667 | 387 / 184 | 4 |
| Aaron Judge 2024 | 54849 | 3 | 2025-01-24 | 5.3623 | 359 / 177 | 931 |
| Matt McLain 2024 | 55824 | 2 | 2025-01-24 | 5.6904 | 400 / 186 | 8 |
| Brandon Belt 2023 | 50571 | 3 | 2024-01-26 | 4.9692 | 368 / 179 | 869 |
| Wander Franco 2023 | 51820 | 2 | 2024-01-26 | 5.4357 | 398 / 186 | 137 |
| Jed Lowrie 2018 | 32272 | 3 | 2019-01-27 | 4.7774 | 357 / 169 | 600 |
| Rhys Hoskins 2023 | 51083 | 4 | 2024-01-26 | 5.5132 | 378 / 176 | 21 |
| David Ortiz 2016 | 22760 | 4 | 2017-01-28 | 4.2436 | 398 / 182 | 485 |
| Matt McLain 2023 | 51984 | 2 | 2024-01-26 | 5.4357 | 398 / 186 | 605 |
| Fernando Tatis Jr. 2022 | 47261 | 0 | 2023-01-26 | 5.0648 | 255 / 161 | 34 |
| Adam Engel 2021 | 42722 | 1 | 2022-03-18 | 4.8826 | 322 / 201 | 675 |

Concentration is estimated from earlier active outcomes against nested means,
not from these fourteen realized outcomes. One floored calibration label occurs
in the Ortiz cell where a deterministic boundary mean cannot assign positive
mass to its observed active outcome. The observation was retained; the fitting
floor is recorded. The other case cells have no floored labels.

## Side by side forecasts

Triples are PA P10 / P50 / P90, not expected PA. The proposed middle range is
P10 to P90. Percentages in the p400 column mean at least 400 PA next year, not
a productive season, eventual MLB success or a six-year prospect valuation.

| Player and origin | p | c | Expected PA | New quantiles | Narrow quantiles | Older forest quantiles | p400 | Actual PA |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: |
| Kurtz 2024 | 6.06% | 168.16 | 10.18 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 103 | 0.37% | 489 |
| Langford 2023 | 59.91% | 358.74 | 214.92 | 0 / 194 / 523 | 0 / 345 / 372 | 0 / 0 / 238 | 23.84% | 557 |
| Alonso 2018 | 80.36% | 267.58 | 215.03 | 0 / 199 / 459 | 0 / 263 / 283 | 0 / 0 / 323 | 16.33% | 693 |
| Judge 2016 | 92.50% | 335.05 | 309.92 | 56 / 305 / 561 | 308 / 334 / 352 | 0 / 129 / 499 | 32.59% | 678 |
| Judge 2024 | 99.07% | 535.74 | 530.75 | 315 / 552 / 720 | 518 / 536 / 553 | 426 / 657 / 707 | 79.83% | 679 |
| McLain 2024 | 44.67% | 294.75 | 131.65 | 0 / 0 / 414 | 0 / 0 / 305 | 0 / 0 / 344 | 11.12% | 577 |
| Belt 2023 | 64.63% | 377.77 | 244.16 | 0 / 239 / 559 | 0 / 367 / 392 | 0 / 285 / 632 | 28.91% | 0 |
| Franco 2023 | 99.05% | 564.86 | 559.49 | 350 / 584 / 737 | 548 / 565 / 581 | 224 / 490 / 656 | 84.74% | 0 |
| Lowrie 2018 | 90.65% | 505.98 | 458.68 | 111 / 498 / 703 | 472 / 504 / 523 | 82 / 519 / 672 | 66.96% | 8 |
| Hoskins 2023 | 10.07% | 260.91 | 26.26 | 0 / 0 / 16 | 0 / 0 / 228 | 0 / 0 / 508 | 1.88% | 517 |
| Ortiz 2016 | 0% | 504.66 | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 203 / 619 / 695 | 0% | 0 |
| McLain 2023 | 98.53% | 608.34 | 599.38 | 399 / 632 / 762 | 592 / 608 / 624 | 197 / 490 / 665 | 89.94% | 0 |
| Tatis 2022 | 13.40% | 296.16 | 39.68 | 0 / 0 / 174 | 0 / 0 / 287 | 0 / 0 / 472 | 3.51% | 635 |
| Engel 2021 | 94.24% | 275.86 | 259.97 | 49 / 244 / 493 | 253 / 275 / 293 | 21 / 192 / 478 | 21.27% | 260 |

## Elite prospects and the two Judge forecasts

**Nick Kurtz after 2024.** Age 21, 35 A PA with four HR, seven K and ten
unintentional walks, then 15 AA PA with three K and two walks. No recent MLB PA
or returned roster listing enters the model. Preseason rank score .63 increases
both participation and conditional workload, but zero current MLB workload has
a -99.72 PA path contribution and listing absence -22.65. The conditional head
moves its 278.55 reference to 168.16; p remains 6.06%. With 93.94% probability
at zero, even P90 is zero. This is mathematically correct, not zero hitting
talent, and the full distribution still has a tail. The actual 489 PA sharply
contradict the immediate-readiness forecast. Global spread cannot rescue a
6% arrival probability; the refined active profile has no analogues. Ariza,
Avila, Chevalier and Quero all received zero next-year PA, but broad age/position/
sample matching does not make those players equivalent elite college bats.

**Wyatt Langford after 2023.** Age 21, 200 professional PA, ten HR, 36 walks
and 34 K; 54 AA plus 26 AAA PA are present separately from A+/rookie counts.
The .95 ranking score adds 147.25 conditional PA along saved paths, whereas
zero current MLB workload subtracts 94.00. The head moves 279.20 to 358.74 PA;
the participation logit is .4017, yielding 59.91% p. The new upper quantile
523 is much closer to 557 actual than the narrow 372 or older forest 238,
although the actual remains outside P90. Quantile loss improves from 109.40
narrow and 207.10 forest to 89.27. Both mean and readiness remain low. Crews
received 132 PA, while Montgomery, DeLauter and Teel received zero; genuine
variation in prospect timing does not validate Langford's mean. His refined
active profile also has zero earlier matches.

**Pete Alonso after 2018.** Age 23, 574 AA/AAA PA, 36 HR, 73 walks and 128 K:
273 AA PA with 15 HR and 301 AAA PA with 21 HR. Separate histories include
16 A+ HR in 346 PA the previous year. Minor games and AA role/exposure increase
the participation logit to 1.4091, or 80.36%. The rank path adds 101.56 active
PA, but absent MLB PA and current MLB workload contribute -69.06 and -38.37.
The active head ends at only 267.58, giving 215.03 expected PA. Broader upper
support reaches P90 459 rather than 283 or 323, improving quantile loss, but
693 actual is still far above it. Five refined earlier active matches are weak
support. Thaiss received 164 PA; Rooker, Craig and Lester zero. Similar minor
workload alone does not match Alonso's 36-HR production. The shortage is not
just an interval-width defect.

**Aaron Judge after 2016.** Age 24, 95 MLB PA with four HR, 42 K and nine
walks, plus 410 AAA PA with 19 HR, 98 K and 47 walks. Earlier AA/AAA production
is present rather than erased by the MLB sample. Returned listing and 27 MLB
games increase the participation logit to 2.5123, or 92.50%; recent and previous
rank paths add 97.39 and 60.37 conditional PA. The head moves 276.99 to 335.05,
with current 95 MLB PA contributing -53.87 along paths. P90 rises to 561 from
352 narrow and 499 forest. Quantile loss improves to 118.00 versus 167.47 and
167.80, but actual 678 PA still exceeds the range. Renfroe received 479 PA,
Moya and Waldrop zero, and Teoscar Hernández 95. Four refined active matches
cannot certify future stars. This is a workload result, not prediction of
Judge's subsequent hitting breakout.

**Aaron Judge after 2024.** Age 32, 696/458/704 MLB PA and 62/37/58 HR across
2022–24. Current workload contributes +141.27 PA, age -39.36 and production
quality +33.21 to the active head, which moves 277.92 to 535.74. Listing,
158 games and workload support 99.07% appearance probability. The new 315–720
range includes actual 679, but its quantile loss 34.67 loses to the older
forest's 13.03; the forest median 657 is much closer than 552. It beats the
unrealistically narrow reference's 67.00. Peers Castellanos, Suárez, Yandy Díaz
and Schwarber received 589/657/651/724 PA. A 931-person coarse support count
does not establish star-specific support, and a wide range cannot make the
531-PA mean correct. This counterexample prevents an all-stars improvement claim.

## Availability and return forecasts

**Matt McLain after 2024.** Age 24, no 2024 PA after 403 MLB PA with 16 HR,
115 K and 31 walks in 2023, plus 180 AAA PA with 12 HR that year. The returned
listing input is zero despite the previously reviewed conflict with an October
activation event. The workload path subtracts 93.05 active PA; pooled MLB quality
and role add 38.32 and 36.09. The head ends at 294.75. Listing absence contributes
-.567 to the participation logit; final p is 44.67%, giving 131.65 expected PA.
The new P90 414 is better than 305/344 but below actual 577. Eight refined
active matches do not establish a comparable medical return. Marcano, Franco,
Tejeda and Fox all received zero; legal restrictions and marginal careers are
not medical controls. The uncertainty test keeps the source conflict visible,
does not flip his listing or certify it as the sole cause of the miss.

**Brandon Belt after 2023.** Age 35, 404 PA with 19 HR, 141 K and 60 walks,
after 298 and 381 PA in the two preceding years. He is an unsigned free agent,
not a known retired player. The listing path contributes -.979 log-odds, while
103 current games and historical games contribute +2.581 and +.875; p is 64.63%.
Current workload and quality add 87.67 and 44.24 active PA, leaving c 377.77
and expected PA 244.16. The new range contains zero; quantile loss improves
to 58.47 from 74.23/68.57. That means the outcome was assigned meaningful
probability, not that the method foresaw that nobody would sign him. Martinez,
Blackmon, McCutchen and Canha received 495/499/515/462 PA. Those returns support
retaining this as a reasonable miss rather than making every older free agent
a hard zero. The 869-person profile is not a matched unsigned-market cohort.

**Wander Franco after 2023.** Age 22, 491 PA with 17 HR, 69 K and 39 walks;
344 and 308 PA in earlier MLB seasons. The current opportunity heads receive
listing=1, games and production but not the relevant administrative-availability
state. Listing contributes +2.679 log-odds and games +1.273, yielding 99.05% p.
Workload, age and quality contribute +101.30, +36.86 and +32.44 active PA;
c is 564.86. Even the wider P10 is 350 before zero actual PA. Quantile loss
226.90 beats the narrow 277.93 but loses to forest 170.73. Perdomo, Volpe,
Abrams and Tovar received 388/689/602/695 PA; none is an eligibility control.
This is a known availability-representation problem, not evidence that his bat
was poor. A positive-workload spread cannot alter the wrongly tiny zero mass.

**Matt McLain after 2023.** Age 23, 403 MLB PA with 16 HR and 180 AAA PA with
12 HR, following 452 AA PA and 17 HR in 2022. Listing and MLB games increase
appearance probability to 98.53%; current workload, quality and pooled AAA HR
add 95.65, 33.26 and 32.87 active PA. The head moves 279.31 to 608.34 and
expected PA is 599.38, the largest false-high mean. The new P10 399 is below
592 narrow but still far above zero actual. Forest quantile loss 162.93 is
better than the new 250.43. His later injury cannot be inserted into this
earlier forecast; that would leak the outcome. Allen, Schmitt, De La Cruz and
Neto received 105/113/696/602 PA. Future medical shocks are genuine risk, but
not every individual full-season absence proves the earlier mean unreasonable.
The case demonstrates that neither spread nor a broad 605-person profile
provides full availability protection.

**Fernando Tatis Jr. after 2022.** Age 23, no 2022 MLB PA, but 546 PA and
42 HR in 2021 and 257 PA with 17 HR in the shortened 2020 season. The 14 AA
PA in 2022 remain a small minor sample, not a substitute for his prior MLB bat.
Restricted-list context and a finite suspension are not permanent retirement.
The existing listing input is zero; pooled MLB games add +1.217 log-odds but
listing contributes -.550, leaving only 13.40% p. Zero workload subtracts
94.42 active PA, pooled quality adds 87.84, and c ends at 296.16. Expected
PA 39.68 is the largest false low before 635 actual. The new P90 174 is worse
than narrow 287 and forest 472. Apostel, Welker and Basabe received zero and
Jahmai Jones eleven; these sparse-window controls are not comparable 42-HR MLB
stars. The model compresses a temporary absence and known earlier talent into
an inadequate return forecast. This test cannot resolve finite game suspension,
calendar eligibility or current workload by altering positive spread alone.

## Selected gains and harms and an ordinary case

**Jed Lowrie after 2018.** Age 34, 680 PA with 23 HR, 128 K and 77 walks,
following 645 and 369 PA. Current 157 games and historical games increase the
participation logit despite listing absence, giving 90.65% p. Current MLB PA
adds 94.83 active PA and age subtracts 56.34; c ends at 505.98. He receives
eight next-year PA, not zero, so the positive-workload lower tail matters.
The new P10 111 is much better than narrow 472 but still too high, while
forest P10 82 is closer. Quantile loss falls 239.03 to 135.73 against narrow,
the largest such gain, but loses to forest 129.50. Kinsler, Markakis, Dozier
and Votto received 281/469/482/608 PA. Broadening helps represent a short
active season, but this one result does not establish an injury mechanism.

**Rhys Hoskins after 2023.** Age 30, no 2023 PA following 672 PA and 30 HR
in 2022 and 443 PA with 27 HR in 2021. The current returned listing is zero;
historical games help participation, but final p is only 10.07%. Workload
contributes -88.09 active PA, quality +76.27, and role +25.63, ending at c 260.91
and expected PA 26.26. The new P90 collapses from narrow 228 to sixteen, versus
517 actual; quantile loss worsens to 253.70 versus narrow 190.10 and forest
106.10, the largest harm against both references. This is not an arithmetic
bug: with 89.93% mass at zero, the unconditional 90th percentile corresponds
to roughly the 0.65th percentile of active PA. Broadening the active distribution
adds low positive outcomes as well as high ones, so that particular quantile
falls. His tiny appearance probability is the substantive failure. Marmolejos,
Nogowski, Walding and Mercedes all receive zero, but none is selected to match
Hoskins's prior 672-PA, 30-HR regular status and medical return. A 21-person
refined profile count does not repair that missing comparability.

**David Ortiz after 2016.** Age 40, 626 PA with 38 HR following 614/602 PA
and 37/35 HR. Strong historical production yields a raw conditional output
504.66; workload, current MLB PA and role have positive contributions. The raw
participation logit -.0749 would not itself enforce retirement. The preexisting
reported-retirement rule instead sets final p to zero. Both new and narrow
distributions correctly have all mass at zero before zero actual PA; forest
quantiles 203/619/695 produce loss 187.23. This is the largest forest gain,
but it belongs to an existing context rule, not the new spread. Beltrán,
Victor Martinez, Pujols and Beltré receive 509/435/636/389 PA; age alone is not
retirement. The separate attribution check applies the same origin-known rules
to fifteen reference rows and shows those rules account for 9.68% of the
headline forest gain. The remaining comparison still mixes different means
and features and cannot isolate spread-only improvement.

**Adam Engel after 2021.** Age 29, 140 MLB PA with seven HR, 31 K and eleven
walks; 60 AAA PA with two HR, 16 K and three walks. Earlier MLB PA are 93 in
the shortened 2020 season and 248 in 2019. Listing, current MLB games and
quality support 94.24% appearance; current low workload contributes
-78.33 active PA, with quality +48.20 and pooled quality +40.77. The head moves
285.29 to 275.86, giving expected PA 259.97 before 260 actual. The new
49–493 range is wider than needed for this realization, so quantile loss
17.47 loses to narrow 3.83 but beats forest 26.57. Trout, Jankowski, Refsnyder
and Hamilton receive 499/64/177/23 PA. Trout is an obviously imperfect batting
peer despite similar age/stage/workload distance. A near-perfect mean in one
case neither proves zero uncertainty nor validates all broad ranges. This is
an ordinary statistical tradeoff, not a reason to tune dispersion to Engel.

## Cohort interpretation and review decision

Peers were selected within origin, prior debut and broad stage, using age,
position, current MLB/minor workload and preseason rank, without future outcomes.
Their observed outcomes are shown afterwards. They are not matched on full
batting history, medical circumstances or legal rights. That limitation is
especially important for Hoskins, Tatis, Kurtz and McLain; a generic zero-PA
comparison does not explain away a star/readiness miss.

The fourteen walks explain both the favorable proper scores and their limits.
Upper-minors forecasts still expect only 32.5 players reaching 400 PA against
59 actual. Thin newly drafted players expect 746 PA against 1,647, although
their expected appearance count 7.39 is close to seven actual. Thus getting
the number of debutants roughly right can conceal failure to identify who
will play a full season. Lower-minors high interval coverage is dominated by
next-year non-arrivals, not validation of eventual MLB talent.

Retain the candidate distribution as limited workload-risk research, not a
validated whole-population component or deployable intervals. Evidence is
favorable for currently active MLB and never-debut upper-minors forecasts;
public matched gain is uncertain, lower-level gain uncertain, and current
absences/thin entrants are unresolved or worse. No player override, mean
replacement, stage-specific spread tuning or new forecast is introduced.
The completed review permits the next practical milestone, but cannot certify
full offense uncertainty, future control value or the whole hitter model.

Evidence: [full dated counts inputs paths probability mass and peers](../reports/model-evidence/hitter-workload-risk/cases.json),
[manual case decisions](../reports/model-evidence/hitter-workload-risk/reviewed-cases.json),
[primary scores](../reports/model-evidence/hitter-workload-risk/scores.json),
[retirement attribution](../reports/model-evidence/hitter-workload-risk/attribution.json).
