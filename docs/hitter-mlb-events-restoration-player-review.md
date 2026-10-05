# Player walkthroughs for restoring separate MLB components

2026-10-05. All seventeen fixed cases are reviewed. They explain an actual
matched improvement, plus continuing breakout, transfer and workload misses.
The [result](hitter-mlb-events-restoration-result.md) retains full-cohort errors,
uncertainty, totals and qualifications; the incumbent is not replaced.

## Selection sources and exact calculation

All seventeen cases were fixed before fitting. The mechanical largest incumbent
gain/harm, false low/high and smallest absolute delivered error among actual
200–399-PA cases are already included: Suzuki 2022, Thames 2017, Judge 2016,
Tatis 2021 and France 2018. No case or failed peer was discarded. These
outcome-selected roles explain behavior; they are not independent validation.

The [unchanged source audit](hitter-mlb-events-source-audit-result.md) records
each player's annual MLB numerators/denominators, pooled rates, prior shares and
actual model coordinates. The [preceding complete source walks](hitter-mlb-detail-restoration-player-review.md)
give the same row IDs, ages, information dates, raw MLB/minor/foreign histories,
adjustments, actual folds/routes and origin-selected peers. Those sources and
dates did not change. This review reconstructs those inputs again and traces the
new actual fits, rather than borrowing the earlier forecasts or explanations.

Hitting means future MLB batting wins above its league mean per 600 PA; delivered
value adds the unchanged replacement term, not defense or full WAR. For absent
players, hitting is unobserved, not zero skill. Expected PA is unchanged. The
common past baseline plus the new fitted residual gives the rate. Residual
includes the fitted intercept and every old/new term; all are machine-saved.

Seven added effects plus changes to the old coefficients/intercept exactly equal
the difference from the matched four-summary forecast. Because inputs overlap,
the added terms alone are not the overall change or causal importance. The
100-opportunity prior is preserved, not newly validated; raw MLB is not park-neutral.
Minor/foreign removal probes rebuild affected common inputs while retaining
actual MLB quality and components. Centering the seven components leaves common
MLB production, quality and exposure, so it is artificial, not removing all MLB
history. All probes retain fixed fitted coefficients and are not evaluated substitutes.

| Player and origin | Common baseline | New fitted residual | Matched rate | New rate | Actual rate | Seven new effects | Old coefficient change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Judge 2016 | −0.726057 | +0.447427 | −0.254103 | −0.278630 | +5.329876 | −0.032934 | +0.008408 |
| Thames 2017 | +3.149685 | −0.066352 | +3.069216 | +3.083333 | +0.622421 | +0.026389 | −0.012272 |
| Maitan 2017 | −1.132281 | +0.839199 | −0.299862 | −0.293081 | Unobserved | 0 | +0.006781 |
| Davis 2018 | +1.428279 | +0.973317 | +2.421783 | +2.401596 | −1.518480 | +0.019479 | −0.039666 |
| Wilkerson 2018 | −1.112917 | −0.265761 | −1.359751 | −1.378678 | −1.650306 | −0.030121 | +0.011193 |
| France 2018 | −0.964989 | +0.934448 | −0.024860 | −0.030541 | −1.059985 | 0 | −0.005681 |
| Alvarez 2018 | −0.467743 | +0.932254 | +0.471745 | +0.464512 | +5.647887 | 0 | −0.007233 |
| Nola 2021 | +0.610894 | −0.843750 | −0.266982 | −0.232856 | −0.924711 | +0.070563 | −0.036436 |
| Tatis 2021 | +2.085676 | +1.135085 | +3.261156 | +3.220761 | Unobserved | −0.042717 | +0.002322 |
| Suzuki 2022 | +2.577305 | −0.024137 | +2.598622 | +2.553168 | +1.996717 | −0.037483 | −0.007971 |
| Judge 2023 | +2.756953 | +0.991670 | +3.773990 | +3.748623 | +7.557649 | +0.092994 | −0.118361 |
| Misner 2024 | −0.733207 | −1.338370 | −1.959387 | −2.071577 | −2.025635 | −0.124284 | +0.012094 |
| Perdomo 2024 | −0.264995 | −0.411615 | −0.693141 | −0.676609 | +2.727891 | +0.155603 | −0.139072 |
| Kurtz 2024 | +0.238192 | +0.393186 | +0.653739 | +0.631378 | +5.150009 | 0 | −0.022361 |
| Yoshida 2024 | +1.596821 | −0.204012 | +1.363061 | +1.392809 | −0.443798 | +0.092129 | −0.062381 |
| Lee 2024 | +1.839976 | −0.407633 | +1.311113 | +1.432342 | +0.463100 | +0.182963 | −0.061733 |
| Suzuki 2021 addition | +3.920524 | −0.606153 | +3.374751 | +3.314371 | +1.174589 | 0 | −0.060380 |

No fixed case has an added-feature range warning. Joint support below counts
distinct full/active training people crossing age, stage, workload, quality,
foreign/scouting and K/HR bands; sparse counts remain qualifications. Broad
comparison peers use source/production distance in the actual earlier training
fold, selected without future success. They are not statistical twins.

## Aaron Judge before the rookie breakout

Row 23934, fold 3, tracking, age 24, cutoff 2017-01-28. The source still has
95 MLB PA with four HR/42 K plus 410 AAA PA with 19 HR/98 K and earlier A/AA/AAA.
K shrinks to 33.333%, coordinate +1.03333; coefficient −0.04753 contributes
−0.049112. Walks add +0.011602; all seven terms sum −0.032934. The intercept
is −0.272708. Other changes add +0.008408, leaving a net negative rate change.
Removing minors raises the new fit +0.554563, an artificial representation probe.

New value 0.812359 is below matched 0.825027, incumbent 1.092725 and actual
8.114763 at unchanged 309.9 expected versus 678 actual PA. Both errors worsen
versus matched. Support is only 6/5. Peers d'Arnaud, Alonso and Taylor retain
future rates +0.064, +0.367 and −2.038. Valid poor-debut evidence under a less
shrunk component prior worsens this exceptional breakout; no source bug is found.

## Eric Thames remains the largest harm

Row 27981, fold 4, tracking, age 30, cutoff 2018-01-27. Latest MLB is 551 PA,
31 HR/163 K/70 unintentional walks; older KBO is 529/595 PA with 40/47 HR.
MLB walks shrink to 11.982% and contribute +0.069487, against K −0.039964.
The seven terms add +0.026389, old changes −0.012272 and intercept −0.350170;
the already excessive common baseline remains largely intact. Foreign removal
lowers the fitted rate −2.396396, not a validated new translation.

New value 3.650377 versus matched 3.639922, incumbent 1.641053 and actual
1.143565 worsens the major miss; expected PA stays 444.4 versus 278. Support
is 0/0. Kang's earlier peer succeeds at +2.658, Park does not appear and Hyun
Soo Kim hits −2.605. Real positive MLB history plus uncalibrated foreign strength
is still not a defensible transfer solution.

## Kevin Maitan has zero observed MLB ability information

Row 31364, fold 4, prospect, age 17, cutoff 2018-01-27. The 176 rookie PA with
two HR/49 K remain; no MLB source is invented. All seven centered inputs/effects
are exactly zero. Relearning older terms adds +0.006781, with intercept −0.284886.
Removing minor production raises the fit +1.093002 under fixed parameters.

Expected PA stays 1.985 and value rises slightly 0.005115 to 0.005137, actual
zero. Conditional rate is not scored, nor is lifetime failure established.
Support is 2682/3; Jhan Rodriguez, Starlin Balbuena and Cesar Mejia all fail
to appear next year. The active talent shortage is not cured by adding MLB-only inputs.

## Khris Davis partially improves but the decline remains missed

Row 32325, fold 3, tracking, age 30, cutoff 2019-01-27. MLB 2018/2017/2016
has 654/652/610 PA and 48/43/42 HR. Pooled HR 6.737% adds +0.030611; K 27.632%
subtracts −0.029766. Other component terms leave +0.019479, offset by −0.039666
from old changes and intercept −0.398151. No foreign/minor removal effect exists.

Rate falls modestly +2.422 to +2.402 against actual −1.518. New value 4.056810
versus matched 4.076081 and actual 0.292742 remains a major miss at 572.8 versus
533 PA. Support is 9/9; Frazier, Dozier and Morales later hit +0.795, −0.415
and −1.828. Components contain truthful strength, not advance knowledge of decline.

## Stevie Wilkerson improves rate but loses delivered closeness

Row 32754, fold 3, tracking, age 26, cutoff 2019-01-27. Latest MLB 49 PA,
no HR/16 K and minor 86 AAA/21 AA/six rookie PA remain. K/BB/HR terms contribute
−0.020402/−0.010719/−0.008081, partly offset by other terms. Seven effects total
−0.030121 and old changes +0.011193, moving −1.360 to −1.379 toward actual
−1.650. Intercept is −0.398151; removing minors adds +0.975163.

Value falls 0.089138 to 0.085683, farther from actual 0.118958 because expected
109.5 PA remains below 361. This reverses some favorable error cancellation.
Support is 341/209; Martinez later has just 19 PA/−8.876, Mejia and Perkins
do not appear. Their tiny/absent outcomes are retained, not interpreted as stable ability.

## Ty France remains the ordinary case with cancelling errors

Row 34339, fold 1, prospect, age 23, cutoff 2019-01-27. Sources still include
479 AA PA with 17 HR/70 K/25 HBP and 110 AAA PA with five HR/19 K/two HBP,
plus earlier A/A+/AA. No MLB counts means seven zero effects. Old changes
−0.005681, intercept −0.250000 and residual +0.934448 move rate −0.024860 to
−0.030541. Minor removal raises it +0.815398; that is not a substitute forecast.

Value 0.263560 nearly matches actual 0.263992, versus prior 0.264384. Yet
87.0 expected PA is far below 201 and hitting −0.031 far above actual −1.060;
opposing errors still cancel. Support is 1444/326. Bandy, Puello and Pohl all
fail to appear next year. This near tie in final contribution does not validate
the talent or workload submodels.

## Yordan Alvarez remains a predebut false low

Row 35088, fold 2, prospect, age 21, cutoff 2019-01-27. His 379 AA/AAA PA,
20 HR/92 K plus older A/A+ and 57 DSL PA are unchanged. No MLB input is
invented. Seven effects are zero; old changes −0.007233 and intercept −0.355953
leave new rate +0.464512. Minor removal raises the fit +0.360185.

Value 0.278176 versus matched 0.279046 remains far below actual 4.609983 at
72.2 expected versus 369 actual PA and actual +5.648 hitting. Support is 1398/318.
Sánchez does not appear; Singleton and Pederson later hit −1.193 and −2.106,
the latter on 38 PA. Separate MLB components cannot directly repair a player's
predebut evidence or identify every breakout.

## Austin Nola has low strikeouts before a later decline

Row 42235, fold 2, tracking, age 31, cutoff 2022-03-18. MLB is 194 PA/two HR
in 2021, actual shortened 184/seven in 2020 and 267/ten in 2019, plus AAA.
Pooled K 17.792% contributes +0.071813; seven effects +0.070563 are partly
offset by old changes −0.036436. Intercept −0.642782 and the full residual
move −0.267 to −0.233, farther from actual −0.925. Minor removal lowers it −0.137476.

Value rises 0.661060 to 0.675044 versus actual 0.632234 at unchanged 245.9
expected versus 397 actual PA. Support is 197/118. Flaherty and Shane Robinson
later have 22/35 PA and extreme negative rates; Clint Robinson is absent.
The component correction is plausible from past contact but not a correct decline forecast.

## Fernando Tatis Jr. remains a high talent forecast with no playing time

Row 43296, fold 0, tracking, age 22, cutoff 2022-03-18. Latest 546 MLB PA/42
HR and 974.8 weighted recent MLB PA remain, with just 4.8 weighted AA PA.
K subtracts −0.059597, walks add +0.021160 and HR +0.015519; seven effects
total −0.042717. Old changes add +0.002322; intercept −0.453174 yields +3.221.
Minor removal changes only −0.020014.

Expected 553.0 PA versus zero actual produces 4.701195 value, modestly below
matched 4.738423 but above incumbent 4.423391. No actual rate exists; do not
relabel absence zero talent. Support is 8/8. Montero, Torres and Sanó later
hit −2.311, +2.014 and +0.908. Conditional components cannot explain away an
availability miss simply because the new delivered error is smaller.

## Seiya Suzuki after entry improves talent but worsens delivered error

Row 47765, fold 1, tracking, age 27, cutoff 2023-01-26. Latest MLB 446 PA,
14 HR/110 K/39 walks plus eleven AAA PA and older NPB 533/514 PA remain.
K 24.359% contributes −0.032400, BABIP 31.915% −0.013456, walks +0.008428;
seven effects −0.037483 and old changes −0.007971 move +2.599 to +2.553
toward actual +1.997. Intercept is −0.450574. Foreign removal lowers it −2.200881.

Expected 406.3 PA versus 583 actual yields value 3.000823, farther from actual
3.765501 than matched 3.031600, but still the largest gain against incumbent
1.380415. Support is only 2/1. Tsutsugo later hits −4.271 while Evans and
Clark are absent. Better talent makes insufficient PA less concealed; do not
claim this alone validates NPB transfer.

## Aaron Judge with established MLB history loses a small amount

Row 50698, fold 3, tracking, age 31, cutoff 2024-01-26. MLB 458/696/633 PA
and 37/62/39 HR remain. Pooled walk rate 13.676% contributes +0.148333, HR
7.561% +0.032614, against K −0.044822, BABIP −0.021854 and doubles −0.020083.
Seven effects sum +0.092994 but old changes subtract −0.118361. Intercept
−0.615584 and full residual move +3.774 down to +3.749.

Value falls 5.030938 to 5.008276 versus actual 11.047280 and incumbent 5.142441
at 536.0 versus 704 PA. Support is 19/19. Stanton, Frazier and Alonso later
hit −1.117, −0.540 and −2.191. Positive component terms do not guarantee a
net upgrade because correlated predictors reallocate; the large superstar miss persists.

## Kameron Misner provides a concrete useful component correction

Row 55509, fold 3, tracking, age 26, cutoff 2025-01-24. The source retains
fifteen MLB PA/ten K, two 519-PA AAA years with 17/21 HR and 510 AA PA/16 HR.
MLB K shrinks to 28.696%, coordinate +0.569565 times −0.160580 = −0.091462.
Walks add −0.027253; seven effects total −0.124284. Old changes +0.012094
leave rate −2.071577 versus matched −1.959387 and actual −2.025635. Intercept
is −0.651904; minor removal raises the fit +0.507895.

Value moves −0.012068 to −0.027873 toward actual −0.054941 at 84.5 expected
versus 217 actual PA. Both errors improve versus matched, though the older
compressed direct rate −2.016 was closer on talent. Support is 641/422; Harrison
and Deichmann are absent, Tucker has 57 PA/−2.859. The useful correction does
not establish fifteen PA as sufficient talent evidence in all profiles.

## Geraldo Perdomo gains a little from his contact profile

Row 55587, fold 1, tracking, age 24, cutoff 2025-01-24. MLB 388/495/500 PA
and three/six/five HR remain, plus 27 latest minor PA. His improving annual
quality is still preserved. Pooled K 17.872% adds +0.121584, walks 10.507%
+0.047373; low HR contributes −0.009242. The seven-term +0.155603 is largely
offset by old changes −0.139072, yielding −0.676609 versus −0.693141.
Intercept is −0.568928; minor removal raises the fit only +0.032889.

Value improves 0.929913 to 0.942934 but remains far below actual 5.521940 at
472.6 versus 720 PA and actual +2.728 hitting. Support is 60/55. Thole and
Schafer later hit −2.993/−2.535; Brantley +0.303. Distinct contact information
helps at the margin, not enough to establish successful trend or breakout prediction.

## Nick Kurtz still lacks useful MLB only inputs

Row 57052, fold 2, prospect, age 21, cutoff 2025-01-24. His fifty pro PA are
35 A/four HR/seven K plus fifteen AA/no HR/three K; roughly 4% common production
share under the original prior. No MLB component is fabricated. New effects
are zero and old changes −0.022361, intercept −0.593412, reduce +0.654 to +0.631.
Minor removal lowers the fit −0.282666.

Expected 10.18 PA versus 489 actual gives value 0.042520 versus matched
0.042899 and actual 5.724344 with +5.150 hitting. Support is 2538/561, not
equivalent rapid-arrival stars. Brooks Lee and DeLauter do not appear; Zunino
has 193 PA/−1.442. This failure remains, without restarting closed jobs tests
or forbidden additional college collection.

## Masataka Yoshida worsens despite real low strikeout evidence

Row 57778, fold 3, tracking, age 30, cutoff 2025-01-24. MLB 421/580 PA and
ten/15 HR coexist with 304.8 weighted NPB PA and eight AAA PA. Pooled K
14.193% contributes +0.141426, walks −0.044015 and other terms leave +0.092129.
Old changes −0.062381, intercept −0.651904, raise +1.363 to +1.393 against
actual −0.444. Foreign removal lowers the fit −0.867393.

Value worsens 2.569032 to 2.592643 versus actual 0.488558 and incumbent
1.746461 at 476.2 versus 205 PA. Joint support is 0/0 after contact bands,
despite coordinate values being in range. Aoki and Suzuki's peers succeed at
+0.661/+1.997, Brosseau is absent. A truthful contact-strength field can compound
optimism where transfer and availability are already wrong.

## Jung Hoo Lee improves value by worsening hitting

Row 58061, fold 1, tracking, age 25, cutoff 2025-01-24. First MLB year has
158 PA/two HR/thirteen K, beside 685.8 weighted KBO PA. Pooled K 13.953%
contributes +0.214475, offset by walks −0.019338 and doubles −0.030391;
the seven terms total +0.182963 and old changes −0.061733. Intercept −0.568928
leaves new +1.432 versus matched +1.311 and actual +0.463. Foreign removal
lowers it −1.856919 under unchanged parameters.

Value rises 0.815567 to 0.846611 toward actual 2.403035, because just 153.6
expected PA is far below 617. Rate accuracy worsens while delivered error improves.
Support is 0/0. Ha-Seong Kim later hits +0.193; Hwang and Hyun Soo Kim are
absent. This positive delivered change is not a successful talent/transfer forecast.

## Seiya Suzuki before MLB remains an unsupported source addition

Row 63309, fold 1, prospect, age 27.37, cutoff 2022-03-18. His three NPB years
supply 1,659 raw PA, 1,311.4 weighted PA and 52.2% production share. No MLB
source or incumbent is invented. All seven effects are zero; old changes
−0.060380 and intercept −0.260143 reduce +3.375 to +3.314. Removing foreign
history lowers the fitted rate −4.058435, an artificial fallback not a new validated model.

Actual rate is +1.175. Expected 191.5 PA versus 446 actual yields 1.657782
value versus matched 1.677051 and actual 2.270747; rate improves, delivered
error worsens. Support is 2/0; Rosario, Nakajima and Meneses all fail to appear
next year. This is separate addition evidence, not a matched incumbent success.

## Reasonability and disposition

All actual new heads replay, sources reconstruct and baseline/intercept/full
terms sum to the saved rates. Added-feature range checks are not joint support.
Negative BABIP coefficients are corrections conditional on an aggregate baseline
already containing batting evidence and correlated quality fields, not causal
claims that hits are bad. Such arithmetic can make baseball sense as a correction,
but must be judged by forecasts and support rather than convenient coefficient signs.

The matched component addition improves both overall errors; several individual
cases still worsen and some apparent value gains hide rate/PA cancellations.
The declared incumbent delivered requirement fails narrowly. Retain the incumbent,
preserve this useful research finding and diagnose the remaining saved error
difference before choosing another fit. No favorable cohort hybrid or 2026 retuning.

Machine traces with full actual source/count/fold/coordinate/coefficient/probe/peer
records are preserved in `reports/generated/hitter-mlb-events-restoration/player-walks.json`
and `reports/model-evidence/hitter-mlb-events-restoration/report.json`.
