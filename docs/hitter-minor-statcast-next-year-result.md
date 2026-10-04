# Minor league Statcast forecast results and player review

2026-10-04. Do not adopt this particular joint minor-tracking forecast. It makes
next-year MLB hitting-rate errors worse, and the player review exposes excessive
influence from tiny minor samples on established hitters. This does **not** reject
Statcast. The previously reviewed MLB addition improved accuracy and remains a
qualified research candidate. Prospect results here are mildly encouraging but
uncertain; the current experiment cannot certify a prospect-only replacement.

## What was compared

The [contract](hitter-minor-statcast-next-year-contract.md) preserved all 30,506
forecasts, current expected PA, historical labels and five whole-player folds.
Training targets had to be completed at the forecast cutoff. Both new Ridge
heads include production, reviewed rankings/pedigree, translated prospect inputs
and the MLB Statcast inputs. The control adds only minor measurement coverage;
the other adds league-specific exit-velocity and launch-angle summaries. No
hyperparameter search or post-result rescue was run.

The combined benchmark uses the existing translated-linear forecast for players
who have not debuted and the reviewed MLB tracking forecast for everyone else.
It is an assembly of useful research components, not a deployed joint model.
Comparison with its coverage control isolates adding the measurement values;
comparison with this assembled benchmark also includes refitting the shared
inputs, rankings and translation together. It is not a pure Statcast ablation.

Source coverage is 2021–24 Pacific Coast, International and Florida State leagues,
not all minor levels. Only 2023 and 2024 origins have sufficient mature tracked
training people to activate the new branch: 3,116 forecasts, including 970 future
MLB participants. The other 27,390 preserve the combined benchmark exactly.
This avoids fabricating early minor coefficients. The 20-person league minimum
is only a fallback rule; many narrower profiles have little or no support.

## Hitting rate and delivered contribution

Rate means next-calendar-year MLB batting wins per 600 PA relative to that future
season's environment. It is custom batting value, not full WAR. Rate scoring
includes actual MLB participants, weights by actual PA within origin and gives
origins equal weight. Non-arrivals have no observed rate but remain in the separate
all-player contribution score. Expected PA is identical in every arm.

| Forecast population | Active rate cases | Combined benchmark RMSE | Coverage control RMSE | Measurements RMSE |
| --- | ---: | ---: | ---: | ---: |
| Eligible minor tracked | 970 | 1.85225 | 1.85069 | 1.89579 |
| Eligible never debuted | 156 | 2.48872 | 2.43071 | 2.41912 |
| Eligible with prior MLB | 814 | 1.78347 | 1.78902 | 1.84117 |

The primary error rises 2.35% versus the combined benchmark; MAE rises from
1.38067 to 1.44509. Paired MSE difference is +.16318, nominal player-cluster
95% interval [.01141, .33105]. Against the coverage control it is +.16897,
interval [.06576, .29179]. Both supported origins worsen: rate RMSE 1.85393 to
1.91361 for 2023 origins, and 1.85056 to 1.87780 for 2024 origins. Forecasts from
2021 are retained but unchanged; no new minor relationship is estimable there.

Never-debuted participants improve about 2.8% versus the combined benchmark, but
only .48% versus the coverage control. Those MSE intervals span zero:
[-.84289, .16930] and [-.32265, .22139]. Their MAE is effectively unchanged versus
the combined benchmark and the sample is only 156 active cases. This is exposed
development evidence, not authorization to pick that subgroup after seeing it win.

Delivered contribution uses expected PA times predicted batting rate plus an
origin-season replacement reference. All-player RMSE changes .451153 to .451434;
the nominal MSE interval [-.00112, .00154] is inconclusive. Measurements lose
to the coverage control's .449835, with MSE interval [.00050, .00251]. Neither
this target nor the public conversion is defense-inclusive WAR or trade value.

Totals illustrate why one aggregate is insufficient. Eligible actual contribution
is 518.36; combined predicts 636.69, coverage 543.74 and measurements 530.99.
That bias improves. But across the entire population actual is 4,264.19, combined
4,155.43 and measurements 4,049.73: the total shortfall increases. In the matched
public cohort, the measurement total is close to actual while individual rate
errors worsen. Do not call this a successful league-total repair. Playing time
and its outstanding public-benchmark gap are unchanged.

## What the individual players reveal

Sixteen player origins covering thirteen people were selected: eleven cases fixed
from the source review plus the largest contribution gain, harm, false high,
false low and an ordinary active case. The numbers below follow the **routed**
forecasts, not raw heads for people who retain fallback. Expected and actual PA
refer to the next year. A zero-PA outcome is not an observed zero batting skill.

| Player and origin | Combined rate | Measurement rate | Actual next MLB rate | Expected PA | Actual PA |
| --- | ---: | ---: | ---: | ---: | ---: |
| Elly De La Cruz 2022 | +.032 | +.032 | -.748 | 119 | 427 |
| Elly De La Cruz 2023 | +.189 | -.425 | +1.886 | 407 | 696 |
| Junior Caminero 2023 | +.308 | +.308 | -.154 | 234 | 177 |
| Junior Caminero 2024 | +.588 | +.094 | +2.175 | 419 | 653 |
| Wyatt Langford 2023 | +1.439 | +1.355 | +.549 | 215 | 557 |
| Nick Kurtz 2024 | +1.024 | +1.024 | +5.150 | 10 | 489 |
| Bryce Eldridge 2024 | +.468 | +.031 | -3.373 | 68 | 37 |
| Juneiker Caceres 2024 | -.142 | -.142 | Unobserved | .067 | 0 |
| Narciso Crook 2023 | -.322 | -.617 | Unobserved | 8 | 0 |
| Brewer Hicklen 2023 | -.536 | -1.419 | -15.356 | 8 | 5 |
| Jimmy Herron 2023 | -.324 | -.560 | Unobserved | 38 | 0 |
| Bo Bichette 2023 | +1.449 | +.122 | -2.243 | 635 | 336 |
| Bo Bichette 2024 | -.019 | -1.105 | +2.424 | 465 | 628 |
| Yordan Alvarez 2024 | +4.030 | +4.078 | +.920 | 547 | 199 |
| Geraldo Perdomo 2024 | -.933 | -.681 | +2.728 | 473 | 720 |
| Michael Massey 2023 | -.329 | -.327 | +.231 | 377 | 356 |

Each saved case includes actual annual stints, measurement dates/counts, all
454 fitted inputs, league reference means/scales and every signed Ridge term,
replayed forecasts, actual future production and four origin-selected peers.
The [additive reporting correction](hitter-minor-statcast-reporting-amendment.md)
preserves stale original display metadata and peers while rebuilding comparisons
from actual fitted feature rows. Fitting and scores never used the stale columns.
Peer distances use age, debut, weighted recent actual PA by level, MLB PA and
draft/rank evidence, never outcomes. Weighted exposures are not literal one-year
PA; the saved dated stints supply those. These peers are diagnostics, not certified
talent matches. In particular, Alvarez's exposure peers are not all elite hitters.

### Elly De La Cruz

In 2022 he had 513 A+/AA PA, 28 HR and 158 K, following a 76-contact FSL sample
in 2021. No league passes the mature-training fallback rule, so no minor head
changes his +.032 forecast. Mead, Luciano and Soderstrom arrive next year;
Cartaya does not. The workload underestimate is not fixed by inventing a rate.

In 2023 he had 186 AAA PA with 12 HR/50 K, then 427 MLB PA with 13 HR/144 K.
His 109 IL readings averaged 93.37 mph, with EV95 116.3. Coverage alone drops
the forecast to -.611; measurements recover it to -.425, still farther from
his subsequent +1.886 than the +.189 benchmark. EV95 contributes +.518 while
mean EV contributes -.237. Those correlated conditional terms and negative
coverage effects do not establish a justified power penalty. There are only
two refined IL training people and one FSL person for his profile. Corrected
peers Alvarez, Matos and Garcia arrive with very different workloads; Diaz does
not. The coverage-driven reduction is a selection-confounding concern, not a
proved causal effect of appearing in AAA.

### Junior Caminero

His 2023 origin has 510 AA/A+ PA, 31 HR/100 K and 36 MLB PA, but no tracked
minor league. Both arms retain the +.308 benchmark. Luciano, Carter and
Crow-Armstrong subsequently appear; Lawlar does not. Missing measurements
are not evidence of poor contact talent.

His 2024 origin has 236 AAA PA, 13 HR/50 K and 177 MLB PA, 6 HR/38 K. The
167 IL readings average 93.27 mph, EV95 111.55 and best-half EV 104.72. The
coverage head lowers rate to +.253; measurements lower it further to +.094
before +2.175 in 653 PA. Current mean EV contributes -.522, EV95 +.189;
harder contact is not therefore physically bad. Only seventeen refined training
people support the profile. Exposure peers Wood and Martínez receive substantial
future PA, Hernaiz fewer and Ramos just twelve. This is a consequential false low.

### Langford and Kurtz

Langford has 200 professional PA, 10 HR/34 K/36 unintentional BB, but only
26 AAA PA and thirteen EV readings. Best-half EV 101.94 contributes +.105.
Measurements are closer than the combined rate to reality but farther than
coverage alone. Expected 215 versus 557 actual PA dominates his value shortfall;
there are zero refined active training people. Draft/rank peers Crews, DeLauter,
Teel and Shaw have no AAA history at origin, and only Crews appears next year.
They are not full-season AAA comparables.

Kurtz has just fifty A/AA PA, 4 HR/10 K/12 unintentional BB and no tracking.
Exact fallback keeps the useful prospect +1.024, not the original model's -.063.
But ten expected PA still misses his 489 PA and +5.150 rate. Cam Smith and
Christian Moore arrive, Wetherholt and Condon do not. Tracking cannot fix a
player for whom the model has no measured contacts; opportunity remains a gap.

### Eldridge and Caceres

Eldridge's 519 PA across four levels contain 23 HR/132 K/56 unintentional BB,
but only 35 AAA PA and twenty tracked contacts. Best-half EV is 101.36 and
hard-air fraction .4. Its conditional signed term is -.252; this is not proof
power should be penalized. The lower rate happens to be closer to his -3.373
over thirty-seven MLB PA, an extremely uncertain talent observation. Refined
support is absent. Miller, Jenkins, Emerson and Clark all have no next-year
MLB PA; none is an identical AAA exposure match. This horizon says nothing
definitive about Eldridge's eventual ceiling or trade value.

Caceres has 167 DSL PA at age sixteen, zero HR/18 K/17 unintentional BB and
no tracking. Both arms keep -.142 exactly. His zero next-year PA and those
of Martínez, Sanchez, Rodriguez and Morillo supply no observed MLB rates.
That is consistent with a long path from DSL, not validation of low lifetime value.

### Crook, Hicklen and Herron

Crook has 325 AAA PA, 10 HR/117 K/40 unintentional BB and 157 EV readings;
2022 IL EV is unknown. Measurements improve over coverage (-.762 to -.617),
but not over combined -.322. Eight expected PA becomes zero actual, so no
rate is observed. Exposure peers Lopez, Young and Oliva do not arrive; Johnson
does. A small contribution reduction is not verified hitting-talent improvement.

Hicklen has 286 AAA PA with 10 HR/70 K/35 unintentional BB after 559 PA with
28 HR/202 K. His 172 readings exist only in 2023. Most of the reduction is
already in coverage (-1.344 versus -.536 benchmark); measurements give -1.419.
The -15.356 actual rate comes from just five PA. It cannot establish a huge
talent decline. Only one refined person supports the profile. Hensley arrives
among peers; Sands, Proctor and Deichmann do not.

Herron has 539 AAA PA, 19 HR/103 K/68 unintentional BB and 467 contacts across
two years. Best-half EV drops 98.23 to 96.43, EV95 104.65 to 102.08. The lower
rate reduces predicted contribution before zero MLB PA, but the fitted hard-air
term is positive for below-reference hard air because its coefficient is negative.
Seven refined people and non-arrival peers Dorrian, Dungan, Mangum and Mendoza
do not turn this conditional association into a clean physical interpretation.

### Bo Bichette

At the 2023 origin he has 1,988 MLB PA across three seasons, versus six AAA
PA/contacts. The new rate falls +1.449 to +.122. It looks successful before his
poor -2.243 future season, but minor mean EV contributes -.382 and angle
dispersion -.308 from **six contacts**. Coverage already cuts to +.807. A lucky
outcome does not justify that amount of influence. Peña, Varsho, Vaughn and
Grisham all appear, with materially different future workloads.

At the 2024 origin he has 1,634 recent MLB PA versus twenty AAA PA and eighteen
measured contacts across two years. The latest angle SD of 9.64 degrees is
-7.35 league reference SDs and contributes -.567; the prior six-contact angle
SD contributes -.429 and current mean EV -.470. Rate falls -.019 to -1.105,
badly missing his +2.424 rebound in 628 PA. Twenty-four refined training people
do not certify this extreme short-sample shape. Nootbaar, Fortes, Hayes and
Carlson provide varied exposure peers, not proof of the angle effect. This is
a specific measurement-precision/role problem, not evidence Statcast is useless.

### Alvarez, Perdomo and Massey

Alvarez has 635 MLB PA, 35 HR/95 K/53 unintentional BB and eight minor contacts
from a prior eleven-PA stint. The rate change +4.030 to +4.078 is small;
547 expected versus 199 actual PA drives much of the false high. His earlier
production did not justify predicting a poor hitter using later injury knowledge.
Castro, De La Cruz, Torres and Devers are exposure peers, not all elite power peers.

Perdomo has 388 MLB PA, 3 HR/58 K/36 unintentional BB and fourteen measured
AAA contacts. Rate -.933 to -.681 improves but still misses +2.728 and 720 PA,
versus 473 predicted. Below-reference hard air yields +.184 because the
conditional coefficient is negative: a lucky direction, not a physics story.
Only six refined training people support it. Kirk, Tatis, Ruiz and Moreno show
different paths; position and batting talent are not matched by this peer rule.

Massey has 461 MLB PA, 15 HR/99 K/24 unintentional BB and eight measured AAA
contacts. Mean angle 39.625 is +5.67 reference SDs, contributing +.281. His new
rate -.327 is nearly the original -.329, while the coverage control is -.993.
Predicted contribution .961 nearly equals actual .959, but expected 377 PA
exceeds 356 and rate/environment errors cancel. That apparent perfection does
not validate eight-contact precision. Doyle, Duran, Sabol and Outman offer
mixed future workloads and careers rather than one favorable success comparison.

## Decision and coherent next work

The experiment is reviewed, not successful. Preserve both original reports and
the metadata correction. Execution, labels, scores, fallback and fitted-head
replays are checked separately from predictive success and baseball judgment.
Comparable-profile adequacy and original provider vintage remain unverified.
The regularized MLB branch remains useful research; the explorer and all thirty-one
protected files remain unchanged. No new forecast is deployed.

The next substantive repair is precision-aware minor measurement integration,
with established MLB evidence protected from tiny minor appearances and a clear
separation between ascending prospects and established players' brief stints.
Counts, known flags and sample products alone did not enforce that behavior.
Freeze a new contract before fitting; do not tune to these sixteen cases, use
arbitrary global discounts, or run another algorithm tournament to avoid the defect.
League centering is not park/opponent neutralization, so that limitation also
remains. Improved short-horizon batting does not resolve the project's playing
time, long-horizon value, defense or control-year questions.

## Literature and reproducible evidence

The literature supports useful velocity information beyond traditional forecasts,
not guaranteed improvement from any implementation. [Sapolsky and Cross](https://tht.fangraphs.com/improving-projections-with-exit-velocity/)
found incremental EV information conditional on existing projections; their
regression was not an independent prospective competition. [Andrews](https://blogs.fangraphs.com/the-doomed-search-for-a-perfect-way-to-interpret-exit-velocity-data/)
demonstrates the importance of the EV summary and sample size, not a universally
optimal cutoff. [Carty](https://fantasy.fangraphs.com/introducing-the-bat-x/)
describes a tracking/traditional blend with regression and aging; reported gains
are developer backtests, not certification of our minor-level integration.

Code, fixed contracts, calibration, support, original cases, corrected reviewed
cases, twenty saved heads and compact predictions are preserved in
`reports/model-evidence/hitter-minor-statcast-next-year`. Full feature frames and
original prediction tables remain local with hashes rather than duplicated in
Git. The additive final receipt records endpoint reconstruction, independent
scores, player review, tests and protected-file checks. Old provisional receipts
remain unchanged. No repeated team-record testing or additional college collection.
