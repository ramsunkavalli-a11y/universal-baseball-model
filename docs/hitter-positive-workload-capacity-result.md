# More flexible playing time models did not improve the hitter candidate

2026-10-04. Keep the existing shallow conditional-workload model. The two locked
challengers slightly worsen overall playing-time and delivered-offense accuracy.
They help some players, but do not fix the important debut, return and hitting
misses. This comparison is closed: no parameter sweep or favorable-group hybrid.
Team-record testing remains separately closed by the user's instruction.

## What changed and what stayed fixed

The [contract](hitter-positive-workload-capacity-contract.md) tests conditional
MLB plate appearances: how much a hitter plays next calendar year if he gets any
MLB PA. The existing appearance probability and hitting-rate forecast stay fixed.
Expected PA is appearance probability times conditional PA. Delivered offense
is expected PA times the fixed batting-plus-replacement yield. These custom win
units are not full WAR, official FanGraphs WAR or six-year club-control value.

All models use the same 251 workload inputs, the original active training rows
and weights, and all 30,506 evaluation forecasts for 11,020 people. There are
seven origins, 2016–18 and 2021–24, with next-year outcomes through 2025.
Non-arrivals and exits remain scored at zero delivered contribution, not zero
hitting ability. No target-2020 training rows or protected 2026 results are used.
The canceled minor season is not treated as poor performance. Coming-preseason
ranking dates and retrospective-source qualifications remain unchanged; these
are not identical information dates to every public forecast archive.

The anchor has depth-three histogram trees. The first challenger has depth-six
histogram trees; the second is LightGBM with depth six and thirty-one leaves.
Both retain 250 iterations, minimum leaf thirty, learning rate .05 and L2 ten.
There is no tuning, new feature, median routing or conditional-on-future-arrival
evaluation. LightGBM's different binning/split rules are part of the comparison;
this does not perfectly isolate capacity alone. Installed versions are
scikit-learn 1.7.2 and LightGBM 4.7.0.

## Matched results

Lower error is better. Scores equally weight target years; totals are raw sums
across the fixed cohort. The public comparison has the same 2,627 forecasts for
1,044 people in 2022–25, including later non-arrivals. It is not a comparison
covering all seven historical years or every prospect.

| Forecast | Public PA RMSE | Public PA MAE | All-player offense RMSE | All expected PA |
| --- | ---: | ---: | ---: | ---: |
| Current | 138.330 | 106.411 | .453384 | 1,228,733 |
| Deeper histogram | 138.797 | 106.572 | .454681 | 1,227,559 |
| LightGBM | 138.943 | 106.671 | .454954 | 1,227,295 |
| Steamer on public matches only | 135.379 | 92.083 | Not an all-player comparison | Not an all-player comparison |

Actual cohort PA is 1,270,493. Actual public PA is 660,776; current/deep/LightGBM
predict 649,255/648,221/648,910. No additional players disappear in the challengers.
All-player contribution totals are 4,165.85/4,162.14/4,159.86 versus 4,264.19 actual.
These cohort sums are not full-league WAR budgets.

Public contribution RMSE is 1.060504/1.060766/1.062163 versus converted Steamer
1.118659. That conversion retains the previously documented environment and
snapshot-date qualifications; it does not establish superiority in hitting
talent or official WAR. Hitting and appearance scores are unchanged by design.
The current public MAE remains 15.56% above Steamer, outside the practical
plan's 15% allowance. Neither challenger closes it or improves the anchor.

The nominal player-clustered 95% paired intervals are development diagnostics,
not fresh holdouts or corrections for repeated historical experimentation.
For public PA MSE, deep-minus-current is +129.50 [-135.73, +378.38]; LightGBM
is +169.98 [-94.63, +432.33]. The uncertain public contrast is not proof of a
useful gain. On all players, PA MSE differences are +54.46 [24.28, 86.29] and
+53.36 [19.37, 88.44]. Contribution MSE differences are +.001178
[.000011, .002493] and +.001426 [.000273, .002589]. Neither new construction
has evidence for replacing the existing head.

## Cohorts and baseball checks

The deeper histogram model worsens whole-population PA RMSE in six of seven
origins; LightGBM worsens it in all seven. Both worsen public PA error in three
of four public origins for deep and all four for LightGBM. The result is not
driven solely by the 2021-origin COVID/reorganization case.

For hitters with at least 600 current MLB PA, RMSE goes 136.316 to
139.871/139.572, MAE 107.959 to 111.072/110.624, and mean underprediction
26.668 to 29.374/29.306 PA. For the 200–399 and 400–599 PA bands both also
worsen RMSE and MAE. Small-current-sample players have mixed effects, not a
justification for constructing a post-result subgroup hybrid.

Upper never-debut expected PA remains 74,239/74,277/73,621 versus 92,891 actual;
RMSE slightly worsens despite a small MAE improvement. Lower never-debut PA
falls 7,055 to 6,616/6,650 versus 5,194 actual, reducing overprediction but not
making either full model better. Thin new draftees remain 746/772/784 versus
1,647 actual. Previously debuted but currently absent hitters remain about
17,200 versus 15,309 actual. Neither a universal prospect boost nor a universal
absence penalty follows from these different patterns.

Distinct active training people were counted before fitting. Broad stage/age/rank
profiles are absent for 5,052 forecasts; refined new/thin profiles for 8,420.
Adding current-PA bands to those refined intersections still leaves 8,420 absent
and 12,844 with fewer than twenty people. They remain in headline scores. These
flags describe missing active-profile support, not proof that each forecast is
wrong or that twenty analogues certify elite talent. Current roster listing
zeros are qualified signals, not certified nonmembership.

Raw conditional PA falls below one for 89 deep and 73 LightGBM forecasts. Some
are negative, down to -37.92/-28.45; all are clipped to one before multiplying
by appearance probability. None exceeds 800. Only one clipped deep forecast
later plays: Brian Navarreto, origin 2024, fifteen actual PA versus .049 expected.
No LightGBM clipped forecast later plays. The engineering bound prevents invalid
negative opportunities but does not convert the raw outputs into meaningful
conditional-workload estimates for unsupported profiles.

## Twenty actual player walks

Nine fixed players were selected before fitting. Each challenger additionally
selects its largest PA and contribution gain/harm, largest contribution false
high/low and ordinary active contribution case. Overlaps leave twenty forecasts.
Outcome-selected cases are diagnostics, not independent validation. Every case
has its actual three-year level counts, all 251 model inputs, three replayed
conditional heads, fixed appearance/rate, support and four peers selected without
future outcomes in [the case evidence](../reports/model-evidence/hitter-positive-workload-capacity/cases.json).
The [structured review](../config/hitter_positive_workload_capacity_review.json)
contains the individual judgments and comparisons.

Unless stated otherwise, the three numbers below are current/deep/LightGBM.
Saved histogram node paths and LightGBM additive contributions each reconstruct
their own predictions. Their attributions use different references and cannot
be subtracted as causal explanations of between-model changes. Full histories
and inputs are saved; the following paragraphs identify consequential mechanics.

### Aaron Judge 2024

Row 54849, age 32: 696/458/704 MLB PA and 62/37/58 HR. Conditional PA
535.74/571.13/546.85 times unchanged 99.07% appearance gives
530.75/565.82/541.76 versus 679 actual. Recent workload is strongly positive in
all fits; deep adds more positive work/role accounting. Contribution improves
5.668/6.043/5.786 versus 9.393, deep's largest value gain, but fixed hitting
4.534 still misses realized 6.427 wins/600. Refined workload support is 207.
Ohtani/Ozuna/Marte/Harper receive 727/592/556/580 PA; the upward change is
plausible, but this favorable case does not negate broad harms.

### Donovan Solano 2022

Row 46330, age 34: 203 short-2020 MLB PA, then 344/304; latest four HR,
eighteen walks, 61 K and 34 AAA PA. Conditional PA falls 304.30 to
259.20/254.35; fixed 42.25% appearance gives 128.57/109.51/107.46 versus 450.
Age/listing/role paths offset positive workload and quality; neither new fit
knows his later employment. Contribution falls .377/.321/.315 versus 2.585,
compounding fixed -.117 hitting versus 1.569 actual. Support is 412.
Brantley/Moustakas/Ruf/La Stella have 57/386/57/24 PA, retaining successful and
unsuccessful older returns rather than imposing a universal exit rule.

### Joey Votto 2023

Row 50568, age 39: MLB workload falls 533/376/242 with fourteen latest HR,
plus 103 AAA PA. Conditional PA rises 328.33/352.54/371.81 as pooled-quality
paths increase and negative age accounting weakens. Fixed 43.33% appearance
gives 142.25/152.74/161.09 versus zero actual; contribution .421/.452/.476
worsens. Realized batting rate is undefined, not zero talent. Support is 450.
Gurriel/Donaldson/Longoria/Cabrera have 65/0/0/0 PA. Keep these exits without
pretending a conditional-workload learner predicted retirement.

### Brandon Belt 2023

Row 50571, age 35: 381/298/404 MLB PA, with nineteen latest HR and sixty
walks. Conditional PA 377.77/346.06/373.79 gives 244.16/223.66/241.58 at
64.63% appearance, versus zero actual. Deep's stronger negative age path
reduces contribution 1.035 to .948; LightGBM gives 1.024. This is a numerical
gain, not foresight of his unusual lack of employment after a good year.
Support is 366. Martinez/Blackmon/McCutchen/Canha receive 495/499/515/462 PA;
their workloads oppose a hindsight rule that all comparable older bats vanish.

### Fernando Tatis Jr. 2022

Row 47261, age 23: 546 MLB PA and 42 HR in 2021, then no MLB PA and fourteen
AA PA. Conditional PA improves 296.16/392.97/362.71 through positive previous
MLB work and quality paths, but unchanged appearance is only 13.40%.
Expected PA is 39.68/52.65/48.59 versus 635. Hitting 1.289 is close to 1.271
actual; the main miss is return opportunity. Support is 34 and availability
is flagged. Apostel/Welker/Basabe/Jones have 0/0/0/11 PA but are not equivalent
star-absence cases; their failures do not explain away Tatis.

### Wyatt Langford 2023

Row 53164, age 21: 200 professional PA, ten HR, 36 walks and 34 K, including
54 AA/26 AAA PA. Rank .95 and AAA role lift conditional PA
358.74/378.79/382.14; fixed 59.91% appearance gives 214.92/226.93/228.94 versus
557. Contribution .912/.963/.971 moves toward 1.796, partly offsetting an
optimistic fixed hitting rate .688 versus .077. Refined active new-draftee
support is zero. Crews/DeLauter/Montgomery/Teel receive 132/0/0/0 PA. More tree
depth neither creates analogue support nor assures every ranked entrant a job.

### Nick Kurtz 2024

Row 57052, age 21: fifty A/AA PA, four HR, twelve walks, ten K. Encoded
rank .63 and draft_rank .818 are present; zero current MLB work has a large
negative saved path. Conditional PA hardly moves 168.16/169.75/170.68, and
6.06% appearance gives 10.18/10.28/10.34 versus 489. Fixed -.063 hitting
misses realized 5.289, leaving contribution about .031 versus 5.838. Refined
active new-entry support is zero. Ariza/Avila/Chevalier/Quero all receive zero
PA, but the first three are not equivalent elite-college pedigree comparisons;
their zeros cannot rationalize the miss.

### Bryan Reynolds 2018

Row 34859, age 23: 541 A+ PA then 383 AA PA, with seven HR, forty walks and
73 K in AA. Small/zero MLB exposure, listing and older A-level K have negative
paths; conditional PA falls 81.02/66.58/53.26. Fixed 15.64% appearance yields
12.67/10.41/8.33 versus 546. Contribution worsens .030/.025/.020 versus 4.696,
with -.430 fixed hitting versus 3.312 actual. Support is 224 coarse active
people. Milone/Bishop/Hendrix/Lund receive 0/60/0/0 PA but are not exact AA
skill analogues. Available AA counts are not proof they are represented wisely.

### Ben Rortvedt 2023

Row 51344, age 25: 98/0/79 MLB PA, plus 139 latest minor PA; latest MLB has
two HR, eleven walks and nineteen K. Conditional PA rises
94.22/119.03/109.51, with role/listing and small-current-work interactions.
Fixed 87.33% appearance gives 82.28/103.94/95.63 versus 328. Workload improves,
yet contribution .103664/.130956/.120486 moves away from .102959 because
fixed -1.102 hitting is optimistic relative to -1.669. Support is 388.
Herrera/Pinto/Amaya/Viloria have 114/49/363/0 PA. The old near-exact value
result was component cancellation, not proof of a good role forecast.

### Matt McLain 2023

Row 51984, age 23: 403 MLB PA with sixteen HR, plus 180 AAA PA with twelve
HR. Positive role/power/work paths remain, but refitting lowers conditional
PA 608.34/554.83/581.26. Fixed 98.53% appearance gives
599.38/546.65/572.69 versus zero, deep's largest PA gain. Contribution falls
2.770/2.526/2.647. There is no new evidence anticipating the subsequent
season-long absence; lower forecasts benefit mechanically. Support is 154.
Julien/De La Cruz/Morel/Franco receive 301/696/611/0 PA, retaining outcomes
that would also make blanket conservatism harmful.

### Trea Turner 2017

Row 28740, age 24: 324/447 recent MLB PA, with eleven latest HR, thirty
walks and eighty K. Conditional PA falls 527.13/428.84/468.88 despite positive
current work and role paths; deep also carries negative older AA-power
accounting. At 98.66% appearance, PA falls 520.07/423.09/462.61 versus 740.
Contribution falls 2.198/1.788/1.955 versus 2.842, deep's largest PA harm.
Support is 102. Story/Owings/Russell/Polanco receive 656/309/465/333 PA.
More interactions are not automatically a smarter young-regular forecast.

### Alex Bregman 2017

Row 28797, age 23: 217/626 MLB PA and nineteen latest HR, 53 walks, 97 K.
Conditional PA falls 547.73/450.76/480.79, with refitted correlated MLB-count,
role and triples paths. At 99.00% appearance, PA is 542.28/446.27/476.01
versus 705. Contribution falls 2.757/2.269/2.420 versus 6.534, deep's largest
value harm. Fixed 1.204 hitting misses 3.715 realized. Support is 44.
Gallo/Machado/Sanó/Suárez receive 577/709/299/606 PA; keeping mixed peers
does not make the worsened workload and production miss disappear.

### Ronald Acuña Jr. 2023

Row 51153, age 25: 360/533/735 MLB PA and 24/15/41 HR. Strong work/quality/
role paths raise conditional PA 592.95/618.12/614.90; fixed 99.21% appearance
gives 588.28/613.25/610.05 versus 222. Value rises 5.168/5.388/5.359 versus
.780, both challengers' largest false high. Fixed hitting 3.414 also misses
.251 realized. Support is 81. Soto/Tucker/Ohtani/Alvarez have 713/339/731/635
PA. This preserves short-season risk without claiming his particular later
loss of playing time was knowable at the forecast date.

### Aaron Judge 2016

Row 23934, age 24: 410 AAA PA with nineteen HR, then 95 MLB PA with four
HR and 42 K. Rank scores .56/.70 add conditional workload; small MLB work
and strikeouts reduce it. Conditional PA is 335.05/334.89/336.73, giving
309.92/309.77/311.48 at 92.50% appearance versus 678. Hitting stays -.040
versus 5.557 realized; contribution remains about .94 versus 8.372, both
challengers' largest false low. Refined support is only four active people.
Moya/Waldrop/Renfroe/Brito receive 0/0/479/0 PA; retaining failed prospects
is necessary, not an explanation of Judge's unmodeled breakout.

### Ramón Urías 2024

Row 54894, age 30: 445/396/301 MLB PA and eleven latest HR. A part-time
role path is negative while quality/listing help. Conditional PA
306.29/292.20/311.96 gives 295.98/282.37/301.47 at 96.64% appearance versus
391. Deep's ordinary-case contribution .689491 nearly matches .689583, yet
workload becomes worse and fixed -.409 hitting is optimistic versus -.816.
Support is 505. Senzel/Candelario/Espinal/Rivera receive 0/91/328/127 PA.
Do not replace this inconvenient ordinary case: its precision is cancellation.

### Oneil Cruz 2022

Row 47281, age 23: 361 MLB/247 AAA PA, with seventeen MLB HR and 126 K.
New pooled-K paths are negative alongside positive work, rank and role.
Conditional PA falls 485.99/413.80/426.88, giving 475.03/404.47/417.26 at
97.75% appearance versus forty. Value falls 1.419/1.208/1.246 versus .224,
LightGBM's largest PA gain. Nothing newly predicts a particular later injury;
the smaller forecast happens to help. Support is 170.
García/Castillo/Allen/Abrams receive 482/1/329/614 PA, showing both tails.

### Jordan Lawlar 2023

Row 52882, age twenty: 490 AA/AAA PA with twenty HR, then 34 MLB PA.
Rank .90/.90, AAA role and BABIP lift conditional PA
337.06/411.27/465.65. Fixed 96.04% appearance produces
323.72/394.99/447.22 versus zero, LightGBM's largest PA harm. Value rises
.995/1.214/1.375; batting rate is undefined in the absent target season.
Support is twenty, not a certification threshold. Luciano/Marte/
Crow-Armstrong/Caminero receive 81/242/410/177 PA. An understandable upward
prospect forecast can still harm realized error and must remain scored.

### Kris Bryant 2017

Row 28362, age 25: 650/699/665 MLB PA and 26/39/29 HR. Refitted exposure/
role paths lower conditional PA 614.44/590.80/564.79, giving
610.24/586.76/560.93 at 99.32% appearance versus 457. Contribution falls
5.506/5.294/5.061 versus 2.707, LightGBM's largest value gain, but fixed
3.567 hitting remains too high versus 1.708. Support is fifty.
Ramírez/Arenado/Rendon/Suárez have 698/673/597/606 PA. This partial gain
does not demonstrate new foresight of the shorter workload.

### Charlie Blackmon 2016

Row 22966, age 29: 648/682/641 MLB PA with 29 latest HR. Positive workload
and role accounting weakens in the new fits; conditional PA falls
626.01/576.16/556.66. Fixed 99.42% appearance gives 622.36/572.80/553.41
versus 725. Contribution falls 3.869/3.561/3.440 versus 8.000, LightGBM's
largest value harm, while fixed 1.879 hitting misses 4.769 realized.
Support is 114. Fowler/Desmond/Dozier/Belt receive 491/373/705/451 PA.
HBP-associated paths are not evidence of a causal durability mechanism.

### Lourdes Gurriel Jr. 2023

Row 51377, age 29: 541/493/592 MLB PA with 24 latest HR. Workload is the
largest positive path; conditional PA barely changes 521.28/516.07/519.35.
At 99.32% appearance, expected PA is 517.73/512.55/515.82 versus 553.
LightGBM's ordinary-case value 2.081438 nearly matches 2.082083, but workload
is slightly worse and fixed .563 hitting exceeds .401 realized. Support is 375.
Yoshida/Reynolds/Arozarena/Profar receive 421/692/648/668 PA. This is a
reasonable forecast with modest cancellation, not superior component precision.

## Integrity and final decision

All seventy active-subset chronology/profile checks preceded fitting; thirty-five
current heads reproduced first. All seventy new heads independently replay on
every test row, and all current columns, appearance/hitting forecasts and PA/value
products remain exact. Thirteen focused arithmetic/chronology tests pass; pytest
could not write its optional cache, which did not affect assertions.

The first scoring invocation stopped before scores because a join changed row
order. Matching by row ID independently proved the same 30,506 players and
unchanged anchor values. A separate sealed reporting repair restores canonical
order without touching the original sealed runner, models, labels, comparisons
or selection rules. The repair also converts Series membership to explicit lists
to avoid a deprecated API ambiguity. No new models were fitted for this repair.
The [receipt](../reports/model-evidence/hitter-positive-workload-capacity/reporting-amendment.json)
preserves that distinction; scoring and final independent recomputation then pass.

All twenty walkthroughs are complete. Keep the shallow conditional-workload
head and current hitting candidate. There is no useful overall gain to adopt,
no reason to route each subgroup to whichever challenger looked best, and no
reason to repeat this capacity comparison. This does not prove all alternative
workload models are useless; it closes these particular fixed constructions.

Return to the practical plan's hitting-talent and population-coverage milestone:
reconcile current rate inputs and the strongest completed compatible talent
experiments before choosing one substantive replacement. The named cases show
where an unchanged hitting model and thin-entry readiness remain central, not
that another parameter sweep or more team context will solve them. No new college
collection is authorized. The full goal remains active, not certified complete.
The existing research explorer, frozen forecast and protected 2026 stay unchanged.

Receipts: [scores](../reports/model-evidence/hitter-positive-workload-capacity/scores.json),
[paired intervals](../reports/model-evidence/hitter-positive-workload-capacity/intervals.json),
[final verification](../reports/model-evidence/hitter-positive-workload-capacity/final-report.json).
