# Count baseline: actual player walkthroughs

2026-10-05. Review performed after the fixed historical comparison. All ten
pre-fit cases remain, plus the largest delivered-value gain and harm and a new
ordinary case. Judge 2016 is also the largest false low; Tatis 2021 the largest
false high. No inconvenient row is dropped. Machine-readable source counts,
graphs, full eight-event logit contributions, forecast probabilities, actual
events, probes and support are in `hitter-count-baseline/player-walks.json`.

Hitting units are next calendar year's MLB batting wins above league mean per
600 PA, conditional on appearing. Delivered value adds the unchanged replacement
rate at unchanged expected PA. This is not full WAR, control years or trade value.
A non-arrival has unobserved hitting ability, not observed zero talent.

## Comparisons and support

The first saved peer rule matches origin-known stage, debut, age, MLB exposure,
draft and scouting; foreign cases also match raw foreign league presence. Those
are demographic peers, not necessarily talent matches. The qualification adds
the past eight-event relative profile to the distance **before inspecting future
outcomes**. Each rule retains three distinct training people and their outcomes,
including failures. Training analogues explain support; they do not independently
validate held forecasts. Generic profile counts below are coarse age/stage/exposure/
scouting/foreign cells, not that many equivalent superstar or elite-draft players.

The fitted calibration has a fixed past-profile offset **plus** learned feature
terms. A coefficient alone omits that offset. The saved trace reproduces all
eight logits and probabilities; partial feature contrasts are not causal effects.
Removal probes hold the fitted model fixed and recompute the source pool and its
derived features, but leave role/history/tracking covariates intact. These are
artificial diagnostics, not replacement forecasts or causal source importance.

## Fixed cases

### Yordan Alvarez, origin 2018, prospect route

His current AA/AAA record is 379 PA, 20 HR and 92 K. Earlier A/A+ records and
57 DSL PA are retained with normalized recency; DSL contributes only 34.2 weighted
PA. The prior gives total production a 37.7% mass share. Level translation leaves
the starting hitting rate at -0.468. Fitted age/scouting/context and event
calibration lift it to +0.481 versus incumbent +0.455. Forecast HR probability
is 3.98%; actual 2019 is 27/369 = 7.32%, with actual hitting +5.648.

PA stays 72.2 versus 369 actual. Delivered value is 0.280 versus old 0.277 and
actual 4.610. Removing minor production raises the fitted rate another 0.293:
the translated profile still pulls down his forecast. This is not old DSL
domination, and the tiny gain does not resolve the breakout. Production peers
are Gary Sanchez 2013 (no next-year MLB PA), Jon Singleton 2013 (362 PA, -1.193)
and Joc Pederson 2013 (38 PA, -2.106). Those outcomes do not justify treating all
young upper-minor sluggers as immediate Yordans. Selected-mover/park-pooled
translation and common shrinkage remain unresolved assumptions.

### Aaron Judge, origin 2016, tracking route; largest false low

He has 95 MLB PA, four homers and 42 K, plus 410 current AAA PA with 19 HR and
98 K and older AA/A records. Minor weighted PA are 1,179.8, not a 57-PA anomaly.
The common starting profile is -0.726; the fitted count rate is -0.171 versus
old +0.264. HR probability rises from baseline 3.10% to 3.65%; actual 2017 is
52/678 = 7.67%. K probability is 31.35% versus actual 30.68%: recognizing his
strikeouts alone does not recognize his exceptional damage and walks.

PA stays 309.9 versus actual 678; value falls 1.093 to 0.868 versus actual 8.115.
Removing minor production raises the fitted rate 0.688. Production peers
d'Arnaud 2013, Alonso 2011 and Michael A. Taylor 2014 produce future hitting
+0.064, +0.367 and -2.038 respectively. Coarse active support is 181 people;
it is not 181 Judges. The older tracking source-year availability is outside the
training range. The new likelihood does not fix this false low, and the graph
profile/strength of strikeout versus damage translation needs a cohort diagnosis,
not a Judge-specific bonus.

### Nick Kurtz, origin 2024, prospect route

Actual professional evidence is 35 A PA (4 HR, 7 K) and 15 AA PA (0 HR, 3 K).
The 1,200 prior makes production only 4% of the initial pool. Baseline +0.238
becomes +0.576, below incumbent +1.024; actual next-year hitting is +5.150.
Predicted HR is 3.48% versus actual 36/489 = 7.36%. Removing his minor evidence
lowers the fitted rate 0.340: this model actually uses the tiny positive sample,
unlike a misleading claim that all small-sample production is ignored.

PA stays 10.2 versus actual 489, dwarfing this talent change; value is 0.042 versus
old 0.049 and actual 5.724. Coarse active support 561 is not elite recent college
support. Production-matched Brooks Lee 2022 and Chase DeLauter 2023 have no MLB
PA next year, while Zunino 2012 has 193 and -1.442 hitting. A general fast-arrival
boost from this one exceptional debut would contradict these origin-selected
comparisons. No new college collection, school or job-model rerun follows.

### Seiya Suzuki, origin 2021, prospect route; source addition

NPB seasons 2019-21 provide 1,659 raw PA, 1,311.4 weighted PA and a 52.2% pool
share. The provisional local-dominance baseline is +3.921, not an MLB equivalency.
The future learner leaves +3.505, forecasting HR 5.59% versus actual 14/446 =
3.14% and hitting +1.175. Removing foreign production lowers the rate 4.478 to
-0.973. The new model genuinely uses his Japanese record but transfers too much
dominance to MLB. His earlier shared-production future/past mix forecast -0.896;
that apparent correction is not a validated intermediate to target.

No incumbent row exists. The fixed research PA reference is 191.5 versus 446;
count value 1.719 versus actual 2.271 looks closer partly because overestimated
hitting offsets underestimated workload. Exact audited profile support is two
full and zero active people. The actual learner sees 15 active NPB-history
people, but just two never-debut active NPB people; zero exact peers does not mean
no NPB training at all. NPB mass is beyond its active feature range, and 2021
reorganization/canceled-MiLB indicators are unseen in mature training. Raw-source
and production peers Rosario, Nakajima and Meneses have no next-year MLB PA;
these are weak positive-arrival analogues. Foreign adaptation remains unsupported
where most needed. Do not certify this from the delivered-value cancellation.

### Jung Hoo Lee, origin 2024, tracking route

158 current MLB PA (2 HR, 13 K) coexist with 685.8 weighted KBO PA. Baseline
+1.840 becomes +1.083 versus old -0.646 and actual +0.463. Predicted contact is
reasonable in direction, but HR 2.78% exceeds actual 8/617 = 1.30%.
Foreign removal lowers the forecast 1.713 to -0.630: the KBO record explains
the change, not a new job assumption. PA stays 153.6 versus 617; value rises
0.314 to 0.757 versus actual 2.403.

Coarse exact support is three full/zero active, while broader KBO learner support
is twelve active people, five never-debut. Production peers Ha-Seong Kim 2021
has 582 future PA and +0.193 hitting; Hwang 2017 and Hyun Soo Kim 2017 have none.
The correction helps Lee, but is neither a fully calibrated Korean equivalency
nor evidence that every foreign-history hitter should receive it.

### Masataka Yoshida, origin 2024, tracking route

Two MLB seasons contribute 885 weighted PA (25 raw HR across 1,001 PA), AAA eight
PA and NPB 304.8 weighted PA. The NPB mass share is only 12.7%, but its local
dominance raises the starting baseline to +1.597. The fitted rate is +1.061,
above old +0.327 and actual -0.444. Removing foreign production lowers the rate
0.777; eight AAA PA changes it only 0.005. This is an overseas-production
transfer problem, not a mysterious tiny minor sample driving an established MLB
hitter. Predicted HR 2.63% is relatively close to actual 4/205 = 1.95%, but overall
walk/hit probabilities still imply too much offense.

PA stays 476.2 versus 205. Value rises 1.746 to 2.329 versus actual 0.489: both
hitting and playing-time errors point high, unlike Suzuki's cancellation. Coarse
active support is three; broad NPB active support sixteen. Production peers
Aoki 2012 and Suzuki 2022 succeed (+0.661/+1.997 hitting), while Brosseau 2023
does not appear. This mix shows why a small foreign subgroup's near-correct
total is not sufficient validation.

### Kevin Maitan, origin 2017, prospect route; non-arrival

176 rookie PA contain two HR and 49 K. Translated starting rate -1.132 becomes
-0.753 versus old -0.380. The fitted minor contribution matters: removing it
raises the rate 1.261. PA remains 1.985; expected value falls 0.00485 to 0.00361;
next-year MLB PA/value are zero, with no observed hitting-rate label. Generic
full support 2,682 masks just three active profiles and age/workload extrapolation.
Production peers Jhan Rodriguez, Starlin Balbuena and Cesar Mejia also do not
appear next year. This is conditional next-year uncertainty, not a lifetime
failure verdict on a 17-year-old or a rule to discard DSL/rookie players.

### Geraldo Perdomo, origin 2024, tracking route

388/495/500 MLB PA in 2024/23/22 yield only 3/6/5 HR. Minor current PA are just
27. Baseline -0.265 becomes -0.611 versus old -0.933 and actual +2.728. Removing
minor evidence adds only 0.034, so the later breakout is not hidden by lower-level
dominance. Forecast HR 1.71% versus actual 20/720 = 2.78% still misses new damage.
PA stays 472.6 versus 720; value improves 0.741 to 0.994 but remains below 5.522.
Production peers Thole 2011, Brantley 2011 and Schafer 2011 have future hitting
-2.993, +0.303 and -2.535. This is a partial gain, not breakout detection solved.

### Fernando Tatis Jr., origin 2021, tracking route; largest false high

546 current MLB PA contain 42 HR; three-year weighted MLB PA are 974.8 versus
4.8 weighted AA PA. The baseline +2.086 becomes +3.396 versus old +2.919.
Minor removal changes only -0.015. Conditional power is plausible; PA stays
553.0 but actual next-year MLB PA are zero, so value worsens 4.423 to 4.863
against zero. There is no actual zero hitting-talent measurement. The later
absence cannot be used to retrofit a preseason ability downgrade.

Production peers Montero 2012, Torres 2018 and Sano 2015 have next-year hitting
-2.311, +2.014 and +0.908. Sporting profiles do not guarantee attendance. Unseen
2021 context remains visible. Total no-arrival expected value falls overall,
but its RMSE worsens because large false positives like this can grow.

### Stevie Wilkerson, origin 2018, tracking route

49 current MLB PA contain no HR and 16 K, alongside 86 current AAA PA (4 HR),
21 AA PA and six rookie PA plus earlier A+/AA. Weighted minor PA total 757.4.
Baseline -1.113 becomes -1.350 versus old -1.289 and actual -1.650. Minor removal
raises the rate 0.926: low-power histories are meaningfully used. PA stays 109.5
versus actual 361. Value 0.091 is worse than old 0.102 versus actual 0.119;
opposing hitting/workload errors had made the old delivered forecast look good.
Production peers Luis Martinez 2011 (19 PA, -8.876), Mejia 2017 and Perkins 2017
(both absent) are not an assured full-season group.

## Cases selected after fitting

### Aaron Judge, origin 2023, tracking route; largest gain

458/696/633 MLB PA and 37/62/39 HR establish enormous power. No recent minor or
foreign production remains. Baseline +2.757 becomes +4.455 versus old +3.899;
actual hitting is +7.558. The count-profile HR term and tracking launch angle/
95th-percentile exit velocity add positive HR-versus-other contrasts, while age
subtracts. Forecast HR 7.76% is near actual 58/704 = 8.24%, unlike his rookie
forecast; walks and other offense remain underpredicted. PA stays 536 versus
704; value improves 5.142 to 5.639 versus actual 11.047. High tracking hard-air
samples exceed training feature ranges.

Demographic peers Wong/Ahmed/Bradley are not adequate talent matches. The
production-aware rule instead finds Stanton 2022, Frazier 2017 and Alonso 2018;
their future hitting is -1.117, -0.540 and -2.191. Even these are not Judge-level
future upside certifiers; his extreme profile is unusual. The gain is genuine
for this row, not a warrant to tune a superstar branch after seeing it.

### Khris Davis, origin 2018, tracking route; largest harm

610/652/654 MLB PA with 42/43/48 HR establish past power. There is no minor or
foreign contribution to blame. Baseline +1.428 becomes +3.395 versus old +2.288;
actual hitting is -1.518. The positive common HR calibration restores power
after initial prior shrinkage; predicted HR 7.60% overshoots actual 23/533 =
4.32%. PA stays 572.8 versus actual 533. Value rises 3.948 to 5.005 when actual
is only 0.293. Production peers Frazier 2016, Dozier 2017 and Morales 2013 include
declines, with next-year hitting +0.795, -0.415 and -1.828. This is a real
overprediction/tradeoff, not evidence of a source bug or advance knowledge of
the later decline. No injury explanation is invented from future facts.

### Kameron Misner, origin 2024, tracking route; ordinary delivered result

15 MLB PA contain 10 K; current/prior AAA seasons each have 519 PA with 17/21 HR
and 152/186 K, preceded by 510 AA PA. Baseline -0.733 becomes -2.250 versus old
-1.840 and actual -2.026. The learner's event calibration increases strikeout
probability to 37.51% versus actual 69/217 = 31.80%. It does not magically
identify all components correctly. Removing minor evidence lifts the rate 0.709.
PA stays 84.5 versus 217; value -0.05297 is near actual -0.05494, but partly
because two component errors cancel. Production peers Harrison 2022 and
Deichmann 2021 have no next-year PA; Tucker 2023 has 57 and -2.859 hitting.
The first demographic rule included pitcher Casey Kelly; that exposes why age/
debut similarity alone is not a useful hitter analogy. The supplementary
production-aware comparisons are the relevant ones here.

## Cross-case judgment

The corrected past-only source geometry lets minor/foreign production affect
forecasts materially; it is no longer a mostly ignored residual. The count
objective largely repairs pooled power-frequency underprediction and improves
some minor cohorts. It also makes established sluggers and foreign local stars
too optimistic in important cases. A small subgroup-total improvement cannot
replace calibrated individual distributions, and lucky rate/workload
cancellations cannot validate a component.

This comparison is complete and not adopted. The earlier future/past pooling
failure remains qualified. The current result does not reject detailed minor
production, foreign histories, or count modeling in general. It rejects this
fixed replacement as the full model: delivered error worsens, foreign adaptation
is inadequately supported and six of seven origin hitting scores worsen.
Keep the incumbent and its completed 2026 evaluation unchanged. Do not create a
post-result foreign/minor-only hybrid or rerun closed opportunity experiments.
