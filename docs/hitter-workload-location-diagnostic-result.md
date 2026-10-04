# What expected and typical playing time explain

2026-10-04. Some of the public absolute-error gap reflects how we summarize an
uncertain season, but the underlying projection still has important errors.
Using the saved median lowers public PA absolute error by 5.79, while worsening
squared error and undercounting total playing time. Keep expected PA and the
current candidate unchanged. This is not a new fitted model or a finding that
Steamer reports medians.

## Fixed comparison and scores

The [contract](hitter-workload-location-diagnostic-contract.md) was saved and
source-sealed before scoring. All 30,506 historical forecasts and current columns
match exactly. The saved workload law has no-arrival probability 1-p, and, when
active, a positive beta-binomial workload with the existing conditional mean.
Every median was recomputed; 26 saved heads and thirteen independent scalar CDF
crossings reproduce the reviewed cases. There are no new fits or changed inputs.
Targets are the next calendar year, through 2025, not eventual MLB careers.
The canceled 2020 minor season and short MLB season retain their existing
treatment. These exposed years are development evidence.

Scores give each represented target year equal weight. Public matches are the
same 2,627 forecasts across targets 2022–25, including non-arrivals; the complete
population spans seven origins. Public source dates and opportunity-information
differences remain qualified. Lower errors are better; totals are raw sums.

| Public forecast summary | PA RMSE | PA absolute error | PA total |
| --- | ---: | ---: | ---: |
| Current expected PA | 138.330 | 106.411 | 649,255 |
| Saved median PA | 141.004 | 100.618 | 608,295 |
| Steamer PA | 135.379 | 92.083 | 695,055 |
| Actual | — | — | 660,776 |

Median choice explains about 40% of the numerical mean-MAE gap to Steamer in
this sample. That is a diagnostic arithmetic comparison, not a gain in expected
value. Public median-minus-mean MAE is -5.793 PA, nominal player-clustered 95%
interval [-6.966,-4.688]. The MSE difference is +746.943 PA squared, interval
[457.250,1033.594]. Median absolute error improves in all four public years,
but RMSE worsens in all four. These resamples do not account for every shared
season shock or the project's repeated experiments.

The mean public total is 1.74% below actual; the median total is 7.94% below.
A sum of medians is not an expected league total. The mean minimizes expected
squared error and a median minimizes expected absolute error for a specified
distribution; neither fact establishes that this fitted distribution is right.
The practical mean-MAE goal remains unchanged and unmet. We do not substitute
median PA into player value or claim that public providers optimize the same
statistical quantity.

## Cohorts and baseball implications

| Forecast group | Mean RMSE | Median RMSE | Mean absolute error | Median absolute error | Mean PA total | Median PA total | Actual PA |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| All 30,506 | 60.499 | 62.547 | 20.612 | 18.764 | 1,228,733 | 1,088,806 | 1,270,493 |
| Upper minors never debuted | 55.127 | 60.228 | 18.732 | 15.665 | 74,239 | 25,451 | 92,891 |
| Lower minors never debuted | 7.966 | 7.964 | .622 | .303 | 7,055 | 203 | 5,194 |
| Thin new draftees | 20.291 | 20.777 | 1.620 | 1.189 | 746 | 0 | 1,647 |
| Currently absent previous debutants | 43.844 | 45.922 | 13.139 | 8.357 | 17,187 | 3,237 | 15,309 |

For prospects, medians largely choose no appearance. They improve absolute
error on numerous non-arrivals but erase expected contributions of rare actual
arrivals. Zero next-year median is not zero talent or eventual value. With
current MLB PA at least 600, median MAE improves 107.959 to 100.220 and RMSE
136.316 to 135.591; equal-year bias improves -26.668 to -1.334. That useful
regular-player distinction cannot justify routing only that favorable group to
the median after results. The 1–199, 200–399 and 400–599 current PA groups all
have worse median RMSE. Complete groups, origins and intervals are saved.

## Thirteen actual player walkthroughs

Each origin below uses season-end production with the following preseason
ranking vintage; it is not a certified December 31 or refreshed Opening Day
forecast. Raw histories, all 251 encoded inputs, actual tree paths, concentration,
calibration hash, CDF crossings and four peers per case are in
[the saved traces](../reports/generated/hitter-workload-location-diagnostic/cases.json).
Path contributions explain a fitted calculation, not causal effects. Support
counts below refer to the broad refined active-training intersection, not
close talent, injury or job analogues. Peers were selected from origin-known
information and cannot explain away a focal player's miss.

**Aaron Judge, origin 2024, row 54849.** His three seasons have 696/458/704 MLB
PA and 62/37/58 HR. Actual inputs include 158 current games and listing=1.
Current work contributes +141.27 conditional PA along his saved path, age
-39.36; these do not imply that age alone caused the miss. Participation 99.07%
times conditional 535.74 gives mean 530.75. The law's median 552 is closer to
679 actual, but still 127 PA short. Support is 931 broad active people.
Ohtani, Ozuna, Marte and Harper received 727/592/556/580 PA. The median helps
a regular without fixing the superstar's expected workload or hitting talent.

**Nick Kurtz, origin 2024, row 57052.** There are 50 A/AA PA, four HR, twelve
walks and ten K. The model receives draft rank .818 and scouting score .63;
pedigree is not missing. Positive scouting paths still end at 6.06% participation
and conditional 168.16, or 10.18 expected PA. With 93.94% zero mass, median
zero is mathematically correct for the saved law and baseball-inadequate for
the realized 489 PA. Active profile support is zero. Ariza, Avila, Chevalier and
Quero all had zero future PA, but their thin-history matches are not equivalent
elite hitting prospects. Neither that peer outcome nor median arithmetic repairs
readiness.

**Wyatt Langford, origin 2023, row 53164.** His 200 professional PA span rookie
through AAA, including 80 AA/AAA PA, ten HR, 36 walks and 34 K. Scouting score
.95 enters both heads and contributes +147.25 conditional PA on the saved path.
Participation 59.91% and conditional 358.74 give mean 214.92. Median 194 is the
16.54th percentile of positive workload, because 40.09% of the mixture already
lies at zero. It worsens the shortfall against 557 actual. Active support is
zero; Crews got 132 PA, DeLauter, Montgomery and Teel zero. An observed elite
success does not mean every similarly drafted player should have guaranteed PA.

**Pete Alonso, origin 2018, row 33263.** The source supplies 574 AA/AAA PA,
36 HR, 73 walks and 128 K. Ranking adds +101.56 conditional PA on his path,
while absent current MLB work has negative contributions. Participation 80.36%
times conditional 267.58 gives mean 215.03; median 199 makes the miss against
693 actual worse. Active support is five. Thaiss, Jones, Lowe and Bradley
received 164/0/169/49 PA. These failed/partial timing controls remain visible,
but do not certify a good full-season readiness forecast for Alonso.

**Bryan Reynolds, origin 2018, row 34859.** He has 383 AA PA, seven HR, 40 walks
and 73 K after 541 A-plus PA. The actual heads receive AA exposure; current
MLB quality=0 denotes no MLB history, not no minor talent. Participation 15.64%
and conditional 81.02 give only 12.67 mean PA. Median zero follows from 84.36%
zero mass versus 546 actual. Both participation and active workload miss badly.
Support 224 is a coarse intersection. Milone, Bishop, Hendrix and Lund received
0/60/0/0 PA, not evidence that Reynolds's productive profile was well represented.

**Brandon Belt, origin 2023, row 50571.** The histories contain 381/298/404 MLB
PA and 29/8/19 HR. With positive quality, 103 games and listing=0, there is no
hard-zero rule. Participation 64.63% times conditional 377.77 gives mean 244.16;
median 239 barely changes the error against no return. This remains a reasonable
nonzero projection that missed an unusual outcome, not a blanket aging penalty
to implement. Martinez, Blackmon, McCutchen and Canha all returned for
495/499/515/462 PA. Those peers specifically caution against learning certain
non-return from Belt alone.

**Wander Franco, origin 2023, row 51820.** The source has 308/344/491 MLB PA,
7/6/17 HR and listing=1. It flags qualified availability but not hard exclusion;
sporting-history paths produce 99.05% participation and conditional 564.86.
Mean 559.49 and median 584 both fail against zero actual PA. A shifted summary
does not resolve the availability scenario. Perdomo, Duran, Abrams and Witt
received 388/285/602/709 PA, but sporting analogues do not match that non-sporting
circumstance. This diagnostic supplies no new future legal information.

**Kevin Maitan, origin 2017, row 31364.** Age 17, shortstop, 176 rookie PA,
two HR, ten walks and 49 K are received alongside scouting information.
Participation 1.52% and conditional 130.37 give mean 1.99 and median zero,
against zero actual next-year PA. Active profile support is zero; Garcia, Sosa,
De La Torre and Nova also had no next-year MLB PA. Low immediate appearance
probability is sensible here. The horizon says nothing conclusive about their
eventual careers or whether Maitan's long-term value was properly priced.

**Joey Votto, origin 2023, row 50568.** This is the largest public absolute-error
gain selected after scoring. MLB PA fall 533 to 376 to 242; inputs include age
39, 65 current games, listing=0 and left-truncated career history. Participation
43.33% times conditional 328.33 gives mean 142.25. Median zero removes that
error when actual PA are zero because the no-return atom is 56.67%, not because
the diagnostic found a retirement fact. Gurriel, Donaldson, Longoria and Cabrera
received 65/0/0/0 PA. Even this older group was not uniformly absent.

**Donovan Solano, origin 2022, row 46330.** The largest public harm is an
opposite example: 203 short-2020 PA, then 344 and 304, with four HR, 18 walks
and 61 K in the last year. Current games/work/quality paths are positive, but
listing=0 contributes -.955 log odds in the saved classifier. Final participation
42.25% and conditional 304.30 give mean 128.57. Median zero then loses those
128.57 PA against actual 450. This is a participation/return underestimate,
not resolved by dropping expected risk. Brantley, Moustakas, Ruf and La Stella
received 57/386/57/24; neither unsigned status nor age guarantees absence.

**Matt McLain, origin 2023, row 51984.** The largest median false high has
403 MLB PA, sixteen HR, 31 walks and 115 K, plus 180 AAA PA and twelve HR.
Listing=1 and positive current work, quality and AAA power yield 98.53%
participation and conditional 608.34. Mean 599.38 becomes median 632 against
zero actual PA. No injury information changes; do not infer that this later
absence was predictable from those origin statistics. Julien, De La Cruz,
Morel and Franco received 301/696/611/0. Broad support 605 is not matched injury
timing. Raising the median worsens a genuine availability miss.

**Fernando Tatis Jr., origin 2022, row 47261.** The largest median false low
has no current MLB PA and fourteen AA PA after 546 MLB PA and 42 HR in 2021.
His 257 PA in short 2020 remain explicit. Listing=0 and an availability scenario
are supplied, not a permanent exclusion. Older work contributes positively, but
participation is only 13.40%; conditional 296.16 gives mean 39.68 and median
zero versus 635 actual. Apostel, Welker, Basabe and Jones received 0/0/0/11,
but are weak star-return analogues. Their outcomes do not excuse this major
return error. Existing source ambiguities and earlier return tests still matter.

**Starlin Castro, origin 2016, row 23376.** The closest ordinary active median
case has 569/578/610 MLB PA and 14/11/21 HR. Actual age is 26 despite coarse
support age_band=3; do not interpret that encoded band as literal elderly age.
Listing=1, 151 current games and workload paths yield 98.05% participation and
conditional 466.57. Mean 457.47 becomes median 473, exactly 473 actual. Gennett,
Hernández, Panik and Schoop received 497/577/573/675. No tuning targeted this
exact result. It checks an ordinary calculation, not independent confirmation
that the distribution or total allocation is correct.

## Decision and next work

All thirteen reviews are complete. The distinction between expected and typical
seasons is real and useful to explain, but does not improve the expected-value
candidate. Keep means, benchmark thresholds, both explorers and protected 2026
unchanged. The eight focused arithmetic and distribution tests pass; those tests
establish calculation integrity, not predictive adequacy.

The large residuals span different problems: weak entry probabilities for
productive prospects, too-low conditional workloads for some entrants, regular
workload regression, uncertain veteran employment, and exceptional availability.
Prior specialized-workload, employment, direct-value and arrival-history tests
have already addressed versions of these ideas; do not repeat their small
patches or infer a blanket prospect/return boost from famous successes.

The next useful step is a fixed-cohort error budget that measures the relative
contributions of participation allocation, active workload and hitting yield on
public/current MLB players and never-debut groups. Reconcile those contributions
with the completed tests before selecting a structural repair. That accounting
may use realized outcomes to diagnose errors, never to generate forecasts or
choose favorable subgroups after results. Full value, supported longer horizons,
cohort readiness and the public mean-MAE gap remain unresolved; the goal stays
active.

Evidence: [scores](../reports/model-evidence/hitter-workload-location-diagnostic/scores.json),
[paired intervals](../reports/model-evidence/hitter-workload-location-diagnostic/intervals.json),
[execution checks](../reports/model-evidence/hitter-workload-location-diagnostic/verification.json)
and [completed review](../reports/model-evidence/hitter-workload-location-diagnostic/final-report.json).
