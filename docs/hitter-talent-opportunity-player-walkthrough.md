# Player review of hitting estimates and MLB opportunity

2026-10-03. Sixteen actual forecast cases were reviewed after the locked test.
Adding the existing MLB hitting estimate to the opportunity models changes
some forecasts, but does not repair the substantial readiness and return misses.
This review supports keeping the existing candidate, not treating this tiny
average gain as a meaningful model improvement.

## What these numbers mean

Each forecast is at the stated origin for the following calendar year's MLB
outcome. Probability means any MLB PA; conditional PA means workload if the
player appears. Expected PA is their product, not a literal predicted season.
Hitting rate is custom batting wins above the target MLB average per 600 PA,
estimated using participant labels weighted by future PA. It is not scouting
FV, position value or validated latent talent for players who never arrive.
Delivered value includes the fixed common-origin replacement reference, not
full WAR. All arms keep that hitting yield unchanged.

The 199 rate inputs preserve three years of level counts; pooled production
uses recency weights 1/.8/.6 and deterministic small-sample priors. The numeric
matrix scales PA and event-rate columns using the saved recipe. There is no
new park/opponent/contact adjustment, published scouting grade, college record
or medical signal in this rate head. Opportunity retains the existing 251
inputs and adds only the generated rate and its known indicator. The control
adds just the known indicator; its actual forecasts equal the current anchor
exactly, not merely approximately in pooled scores.

Every rate estimate excludes the whole tested player group and later outcomes.
The saved intercept plus all 199 scaled-input times coefficient terms reproduces
each estimate. Current and new opportunity heads were independently replayed.
Path effects below are count-weighted within-fit decompositions, not causal
effects or the whole difference between two refitted models. A positive direct
rate path can coexist with lower PA because other splits changed.

## Selection and comparison limits

Nine fixed cases, largest squared-error gain and harm against both controls,
major false high/low and an ordinary active case produced fourteen original
cases. The scorer mistakenly selected Juan Soto's ID for the intended Peña
case. Both are reviewed, with Peña added in a preserved supplementary receipt;
no score, source identity or forecast changed. The sixteenth case is the highest
projected hitting rate among origin-2024 lower-minors players under age 20,
selected without its subsequent outcome. See the
[identity amendment](hitter-talent-opportunity-review-amendment.md).

Four peers per case were selected from origin-known stage/debut status, age,
position, workload, ranking and generated hitting. These are comparison controls,
not interchangeable people. Medical/legal status and full career skill are not
matched; rank and position differences may remain large. In particular, Kurtz's
controls are not equivalently ranked elite draftees, and Tatis's are not
equivalent established stars. Their failures cannot explain away a focal miss.
The complete receipt retains their attributes and distances, including zeros.

Support below is the distinct-player count in the refined participation/active
intersection, not proof of adequate support. The generated rate has its own
participant support, saved separately. Non-arrivals remain in every score.

## Thin entrants and productive upper minors

### Nick Kurtz 2024

Row 57052. Age 21, first baseman, 35 A and 15 AA PA with four HR, 12 walks
and ten K. The known draft-rank input and young age lift the rate estimate, but
it is still -.063 wins/600: intercept -.985, age contribution +.619 and draft
rank +.165, among the complete saved terms. It has no comparable active training
person in the refined profile. Participation support is one, active support zero.

Current 6.06% times 168.16 PA gives 10.18 expected PA. Talent gives 5.72%
times 164.28 = 9.40, versus 489 actual. Value .0307 becomes .0283 versus
5.8378 actual. The direct rate path is -.0139 logit and +1.21 conditional PA;
the model still strongly penalizes absent prior MLB workload. Ariza, Avila,
Chevalier and Kopack all have zero subsequent PA, but much weaker rank signals.
This change hurts and does not provide new information about elite college
readiness. Do not override Kurtz alone or infer every thin entrant will arrive.

### Wyatt Langford 2023

Row 53164. Age 21, outfielder, 200 pro PA including 54 AA and 26 AAA,
ten HR, 36 walks and 34 K. Rate +.688 includes age +.674 and college-draft
classification +.161; his actual upper-level performance is retained rather
than replaced by a same-level label. Refined support is zero for both heads.

Current 59.91% times 358.74 = 214.92 PA becomes 62.32% times 353.96 =
220.58; actual 557. Value .9119 becomes .9359 versus 1.7960 actual. The
rate path adds .121 logit and 20.59 conditional PA within the new fit, yet
conditional PA falls overall after other splits change. Crews subsequently
has 132 PA; DeLauter, Montgomery and Teel zero. A modest gain is plausible,
but neither sparse-support head recognizes a likely full-season workload.

### Pete Alonso 2018

Row 33263. Age 23, first baseman, 574 AA/AAA PA, 36 HR, 73 walks and
128 K after 393 PA in 2017. Rate +.286 includes age +.415 and AAA HR +.123.
His 301 AAA PA and 273 AA PA remain separate inputs. Support is seven/five.

Current 80.36% times 267.58 = 215.03 PA becomes 80.67% times 281.51 =
227.08, versus 693 actual. Value .7649 becomes .8077 versus 6.5980 actual.
There is no direct rate split in his new classifier path; the conditional path
adds 9.45 PA. Rank already adds about 99 PA there, while zero MLB history
subtracts about 69. Thaiss has 164 subsequent PA; Rooker, Craig and Katoh
zero. More workload is reasonable but this still misses both a full season
and a major batting breakout; the extra feature did not repair the hitting head.

### Jeremy Peña 2021

Row 43288, correct MLBAM 665161. Age 23, shortstop, 133 AAA and 27 rookie
PA in 2021, including ten AAA HR and 35 K, after 474 A/A+ PA in 2019.
The canceled 2020 MiLB season is missing, not failed performance. Ranking
score is zero, with the separate listed/known representation retained;
the 40-man indicator is one. Rate -.064 includes age +.437, shortstop -.224
and AAA HR +.119. Participation/active support is 1,533/272, though this broad
intersection does not establish comparable AAA quality or roster opportunity.

Current 26.64% times 176.03 = 46.89 becomes 28.11% times 177.79 = 49.98,
versus 558 actual. Value .1419 becomes .1513 versus 1.3269. The direct rate
paths are -.004 logit and -2.08 PA; the overall small gain is refitting, not
a simple positive talent effect. Weber, Ortiz and Schneemann subsequently have
zero PA; Freeman 86. Their minor PA totals are similar but levels/readiness
are not exactly matched. Strong power in a short AAA sample and roster listing
are already present; simply summarizing them into this rate does not fix arrival.

## Established hitters and the debut contrast

### Aaron Judge 2016

Row 23934. Age 24, right fielder, 410 AAA PA with 19 HR, 47 walks and
98 K; the first 95 MLB PA include 42 K and four HR. The three-year history
also retains 540 AA/AAA PA in 2015. Rate -.040 is near average: age +.283,
pooled MLB quality -.119 and unknown draft-class -.206 are among its terms.
Support is five/four, not robust star-specific evidence.

Current 92.50% times 335.05 = 309.92 becomes 92.86% times 341.71 =
317.31, versus 678 actual. Value .9358 becomes .9581 versus 8.3719 actual.
The new classifier has no direct rate split for him; the conditional direct
rate effect is only +.19 PA. Ranking contributes about +99 PA, while the
small MLB sample and K-rate paths reduce workload. Renfroe has 479 subsequent
PA; Moya, Waldrop and Patterson zero. The tiny PA gain does not discover
Judge's subsequent breakout; both talent and full-season workload are missed.

### Aaron Judge 2024

Row 54849. Age 32, 696/458/704 MLB PA with 62/37/58 HR. Rate +4.534
is driven by real MLB quality: pooled contribution +2.683, recent quality
+1.300, workload +.845 and age -.541, alongside the remaining terms. Broad
support is 1,216/931; there are fewer comparable elite hitters than that count.

Current 99.07% times 535.74 = 530.75 becomes 99.26% times 541.52 =
537.50, versus 679 actual. Value 5.6683 becomes 5.7404 versus 9.3932 actual.
Rate contributes +.249 logit and +14.70 conditional PA, partly offset by refitted
effects elsewhere. Ohtani, Schwarber, Ozuna and Freeman subsequently have
727/724/592/627 PA. Age and mean workload regression remain important; a
plausible six-PA gain does not establish public-system parity or tail calibration.

### Juan Soto 2021

Row 43306, MLBAM 665742. Preserve this mistakenly selected original review
case, without relabeling it Peña. Age 22, 654 MLB PA with 29 HR, 122 walks
and 93 K after 659 PA in 2019 and 196 in the shortened 2020 season. Actual
2020 counts remain raw, while schedule-adjusted workload is a separate feature.
Rate +4.069 includes pooled quality +1.666 and recent workload +.997.

Current 99.40% times 612.09 = 608.42 becomes 99.44% times 608.74 =
605.32, versus 664 actual. Value 6.0323 becomes 6.0016 versus 5.2366 actual:
worse PA but slightly better delivered-value error. Rate's direct paths are
+.207 logit and +3.89 PA, not the net decline. Support 114/99; Guerrero,
Tucker, Tatis and Acuña subsequently have 706/609/0/533 PA. Even excellent
talent does not mean a guaranteed season, and PA improvement alone need not
improve batting value. No future injury/status fact was used as a predictor.

## Availability and major misses

### Matt McLain 2024

Row 55824. Age 24, no 2024 PA after 403 MLB/180 AAA PA in 2023 and
452 AA PA in 2022. Rate +.251 includes retained pooled MLB quality +.436
and age +.310. The returned listing indicator is zero despite the earlier
source audit's activation/listing conflict; this test preserves it rather
than using a synthetic flip as truth. Support 20/eight is limited.

Current 44.67% times 294.75 = 131.65 becomes 43.30% times 292.13 =
126.48, versus 577 actual. Value .4662 becomes .4479 versus .7060 actual.
The new direct rate logit effect is +.125 but probability still falls; absent
workload and listing paths dominate. Franco, Marcano, Tejeda and Fox have
zero subsequent PA but different legal/medical/employment states. Those peers
do not justify the low return forecast. This is a harm with a documented
source/representation qualification, not proof that talent hurts return chances.

### Brandon Belt 2023

Row 50571. Age 35, DH source position, 404 MLB PA with 19 HR and 60
unintentional walks after 298 PA in 2022 and 381 in 2021. Rate +.686 balances
age -.890 with pooled quality +.717 and recent workload +.497. Listing is
zero; support 1,143/869. No retirement hard-zero applies at this origin.

Current 64.63% times 377.77 = 244.16 becomes 63.58% times 371.73 =
236.36; actual zero. Value 1.0353 becomes 1.0022. Rate's direct effects
are positive (+.194 logit, +14.98 conditional PA), yet the complete refit
reduces both outputs. Martinez, McCutchen, Blackmon and Canha subsequently
have 495/515/499/462 PA. A reduced forecast happens to help an unusual
unsigned outcome; it is not evidence that Belt's good season should imply
retirement or justify a blanket zero for productive older free agents.

### Wander Franco 2023

Row 51820. Age 22, shortstop, 491 MLB PA with 17 HR, 39 walks and 69 K
after 344 PA in 2022 and 308 in 2021. Rate +1.035 includes recent workload
+.631 and age +.520. The unchanged opportunity inputs treat listing and
recent production as favorable; unresolved administrative availability is not
represented by this added batting rate. Support 156/137 is not legal-state support.

Current 99.05% times 564.86 = 559.49 becomes 99.22% times 563.34 =
558.97; actual zero. Value 2.6976 becomes 2.6951, essentially unchanged.
Rate directly adds +.283 logit and +5.48 PA, reflecting hitting rather than
availability. Neto, Abrams and Volpe have 602/602/689 subsequent PA; McLain
zero for a different reason. This remains a major availability failure. Do
not rationalize it as unavoidable baseball performance noise or mark it fixed.

### Matt McLain 2023

Row 51984, the largest remaining false-high PA error. Age 23, 403 MLB PA,
16 HR, 31 walks and 115 K, plus 180 AAA PA with 12 HR. Rate +.915 uses
pooled MLB quality +.521, recent workload +.518 and age +.416. Support 711/605.
Current 98.53% times 608.34 = 599.38 becomes 98.53% times 609.52 =
600.59; actual zero. Value 2.7699 becomes 2.7755.

The direct rate paths add +.283 logit and +18.55 conditional PA, offset
elsewhere. Recent MLB work, AAA power and role inputs support substantial
preseason workload; future absence was not a target-time predictor. Neto and
Elly De La Cruz subsequently have 602/696 PA, Franco zero and Duran 285.
Do not assign all these zero outcomes the same cause. A large future miss
does not by itself prove a preseason bug; medical information dates and
availability representation need separate evidence, not tuning this player's PA.

### Fernando Tatis Jr. 2022

Row 47261, the largest remaining false-low PA error. Age 23, 14 AA PA
and no MLB PA after 546 MLB PA with 42 HR in 2021; the 257 MLB PA in
2020 are separately schedule adjusted. Rate +1.289 preserves excellent pooled
quality (+1.009), so this is not ignorance of earlier hitting. Source listing
is zero, and return/status facts are not supplied by the added rate. Support 75/34.

Current 13.40% times 296.16 = 39.68 becomes 13.55% times 294.83 =
39.94, versus 635 actual. Value .2095 becomes .2108 versus 3.3332 actual.
Rate directly contributes +.263 logit and +23.01 PA, yet the overall forecast
barely moves. Apostel, Welker and Basabe have zero subsequent PA; Jones 11,
but they are not similarly talented established stars. Talent summary is
insufficient for this return/availability problem; their failures cannot excuse it.

## Largest changes and an ordinary case

### Oneil Cruz 2022

Row 47281, largest PA squared-error gain against both controls. Age 23,
361 MLB PA with 17 HR and 126 K plus 247 AAA PA; rate -.086 reflects
retained workload, age, position and production. Support 654/559.
Current 97.75% times 485.99 = 475.03 becomes 97.72% times 454.60 =
444.24; actual 40. Value 1.4190 becomes 1.3270 versus .2243 actual.

The direct rate conditional effect is only -3.96 PA, compared with a 31.38
overall conditional reduction. Refitting also reduces workload/ranking path
effects. García, Allen, Castillo and Abrams subsequently have 482/329/1/614
PA. This is not a model predicting the reason for Cruz's future absence:
it trims a still-plausible regular workload and happens to help a large miss.
Keep the gain, but do not advertise it as improved injury forecasting.

### Christian Encarnacion-Strand 2023

Row 52609, largest PA squared-error harm against both controls. Age 23,
241 MLB PA with 13 HR plus 316 AAA PA with 20 HR after 32 minor HR
in 2022. Rate +1.006 includes age +.449, recent MLB workload +.363 and
pooled MLB quality +.186. Support 735/629.

Current 96.76% times 460.17 = 445.26 becomes 97.11% times 499.78 =
485.33; actual 123. Value 2.1254 becomes 2.3167 versus -.5867 actual.
The new rate path adds +.234 logit and +28.09 conditional PA, consistent
with rewarding promising hitting, but realized workload and production both
disappoint. Montero, Gelof, Pratto and Naylor subsequently have 247/547/0/389
PA. This is a plausible talent/workload mechanism that harms the realized
case; it must be counted, not hidden behind improvements on selected stars.

### Greg Garcia 2017

Row 28478, ordinary active case selected by smallest absolute PA error
among actual 200–600 PA seasons. Age 27, source position X, 290 MLB PA
with two HR, 37 walks and 64 K after 257 PA in 2016. Position X is not
a validated specific defensive assignment. Rate -.157 includes workload +.370
and retained AAA K/BABIP contributions. Support 717/553.

Current 95.85% times 218.14 = 209.08 becomes 95.40% times 217.99 =
207.96; actual 208. The direct rate paths are -.0092 logit and -.46 PA.
Workload/role already explain the part-time season. Kivlehan, Tomlinson,
Sánchez and Hernández have 14/152/0/462 subsequent PA. Value .5885 becomes
.5853 versus -.1591 actual: a nearly exact workload forecast still misses
production. This validates neither a batting distribution nor integrated WAR.

## Lower level ability is not established by immediate nonarrival

### Juneiker Caceres 2024

Row 58477. Age 16, right fielder, 167 DSL PA with 18 K, 17 walks,
48 non-HR balls-in-play hits in 126 opportunities, 11 doubles and six triples.
No draft or ranked-list signal is present. Rate +.499 comes largely from
age +1.216 and age-squared +.270 against intercept -.910; position adds +.222.
All DSL-specific terms together contribute only about +.032. Refined active
and rate support are both zero, despite 2,463 participation-profile people.

Current .107% times 62.09 = .067 PA becomes .115% times 96.67 = .111;
actual zero. Rate directly contributes +.097 logit and +18.79 conditional PA.
Amoroso, Baker, De La Cruz and Castillo, selected before examining outcomes,
also have zero subsequent MLB PA. Immediate non-arrival is reasonable, but
it cannot validate this positive MLB hitting number, let alone eventual
prospect value. The quadratic age relationship is learned mainly from older
participants and extrapolated into an unsupported active profile. Keep this
explicit limit in the model card; do not call a teenager better than an MLB
hitter solely because the displayed estimate is positive.

## Cohort conclusions and disposition

The full 30,506-row PA RMSE moves 60.4991 to 60.4295 and offense RMSE
.453384 to .453114, with nominal paired intervals crossing zero for both.
Appearance Brier/log loss worsen slightly. Public MAE moves 106.41 to 106.14
versus Steamer 92.08, still about 15.27% worse, outside the 15% working target.
Upper-minors PA totals fall 74,239 to 74,005 against 92,891 actual. Origin-2021
debut PA moves 10,432 to 10,589 against 18,944; expected debutants 77.63 to
77.77 against 158. The feature does not solve that cohort's undercount.

Keep the existing V68 opportunity and V53/V63 rate/value candidate. Preserve
this generated-rate encoding as a completed, uncertain development comparison,
not a winner, source repair or rejection of stronger hitters earning more PA.
The next useful work is a representation/support audit of the underlying
cross-level hitting estimate before another compressed feature or algorithm
test: distinguish evidence about next-year MLB contributors from unsupported
latent ability for low-level prospects. Reconcile compatible earlier contact
and talent evidence under that same question. Do not invent college inputs,
blanket return boosts or a name-specific fix. No protected 2026 outcomes,
frozen forecasts, explorer changes or deployment; the full goal remains active.

Evidence: [original cases](../reports/model-evidence/hitter-talent-opportunity/cases.json),
[supplementary cases](../reports/model-evidence/hitter-talent-opportunity/supplementary-cases.json),
[review receipt](../reports/model-evidence/hitter-talent-opportunity/reviewed-cases.json)
and [scores](../reports/model-evidence/hitter-talent-opportunity/scores.json).
