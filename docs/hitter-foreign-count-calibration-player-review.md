# Overseas count calibration: player review

2026-10-05. Review complete; candidate not approved. This is historical
development evidence through 2025, not another 2026 evaluation. Read the
[locked contract](hitter-foreign-count-calibration-contract.md) and
[cohort result](hitter-foreign-count-calibration-result.md) alongside these cases.

## Selection and actual calculation

Retain all seven fixed cases, all eleven routed players with next-year MLB PA,
the largest value gain/harm, highest/lowest predicted value, the ordinary
non-arrival with smallest stable MLBAM ID, Soto's other original-cohort harm,
and four newer-MLB controls. This produces eighteen player-origins, not eighteen
independent people. The mechanical artifact contains seventy-two complete
traces, including three origin-selected peers for every focal case:
`reports/generated/foreign-count-calibration/player-walks.json`.

Peers come from the same origin with foreign source evidence. Distance uses
age/5, absolute log1p foreign-PA difference, and two-point penalties for a
different prior-debut state or dated MLB-job hint. Stable player ID breaks ties.
No future outcome chooses peers. These are comparisons, not certified comparable
talents: notably Ohtani has no genuinely similar young, two-way NPB newcomer.
Failed peers remain in the record. No fitted parameter changed during review.

For each league, each observed season's eight mutually exclusive event counts
receive +0.5 smoothing; season probabilities and league references are pooled
by 5/4/3 times observed PA. Their relative centered log ratios feed the actual
held-origin/held-player domestic intercepts/slopes and foreign offsets. Softmax
produces eight coherent probabilities, referenced to held-origin MLB. There is
no park correction, opponent correction, age-development term or scouting input
in this translated talent branch. Age is reviewed for support, not fitted here.
Older MLB talent is discarded when the latest substantial foreign season wins
the route. The 30-PA route floor is coverage, NOT proof of reliable talent.

The event-value differences sum to batting wins per 600 PA. K and other have
zero direct dot-product coefficients; they still affect all probabilities
through the normalization. Expected value equals unchanged participation
probability times unchanged conditional PA times `(rate/600 + replacement)`.
This is batting plus replacement, not full WAR. Non-arrivals have observed
value zero and unobserved hitting rate; a saved numeric rate placeholder is
never interpreted as their actual hitting ability.

All thirty-five saved calibration cells have independently reconstructed source
coordinates, weights, count likelihoods, numerical/analytic gradients and bound
stationarity checks. All seventy-two traces reconstruct source pooling, held
coefficients, expected PA and value. Execution accuracy does not establish that
the baseball choices were sound.

## All routed participants, including the inconvenient ones

The table is exhaustive for this route. Original forecasts use unchanged current
UBM as baseline. Rows marked *added* have no current forecast: their baseline is
the older dated-context domestic anchor, deliberately not the newer shared
opportunity candidate. Every arm uses the same PA within each row. Units for
rates are batting wins per 600 PA relative to the origin reference.

| Player, target season | Baseline rate | Old translation | Count rate | Observed rate | Fixed PA / actual PA |
|---|---:|---:|---:|---:|---:|
| Thames, 2017 | -0.711 | +2.529 | +2.351 | +2.423 | 20.8 / 551 |
| Adduci, 2017 | -1.078 | -0.204 | -0.541 | -0.264 | 3.3 / 93 |
| Dixon, 2022 | -1.147 | -0.639 | -1.174 | -4.542 | 10.5 / 14 |
| Henry Ramos, 2023 | -0.703 | -0.202 | -0.625 | -0.688 | 6.1 / 86 |
| Hyeseong Kim, 2025 | -1.033 | -0.742 | -1.223 | -0.342 | 0.4 / 170 |
| Hwang, 2017, added | +1.763 | -0.039 | -0.351 | -5.451 | 0.5 / 57 |
| Ohtani, 2018, added | +1.927 | +0.652 | +0.840 | +3.693 | 12.3 / 367 |
| Machado, 2022, added | -0.232 | -1.723 | -2.340 | -3.310 | 1.4 / 17 |
| Suzuki, 2022, added | -2.337 | +1.794 | +2.211 | +1.175 | 25.3 / 446 |
| Yoshida, 2023, added | +0.229 | +2.365 | +2.874 | +1.093 | 35.5 / 580 |
| Lee, 2024, added | +0.223 | +1.582 | +1.502 | -1.144 | 31.8 / 158 |

### Thames: good translated talent, severely inadequate opportunity

MLBAM 519346, origin 2016, fold recorded in the artifact. His KBO 2014–16
seasons contain 514/595/529 PA and 37/47/40 HR, versus older MLB 2011–12 work.
The three-year source feeds strong power even after the KBO HR offset of
-0.553 logits and domestic HR slope 0.762. The HR, UBB and doubles value terms
are +0.868, +0.455 and +0.602 wins/600; HBP adds +0.617, a conspicuous
small-mover adjustment, not a proven personal skill. Only three KBO movers
support this held fit; none shares his reviewed age/contact/power intersection.

The unchanged 20.67% participation and 100.49 conditional PA produce just
20.78 expected PA despite positive dated employment evidence. Count talent is
close to actual, but predicted contribution is 0.145 versus 3.925 actual.
The old translation was already closer in talent. This case drives much of
the gain against the domestic baseline; it does not establish the new loss as
better. Peers Park, Pill and Hyun Soo Kim include two non-arrivals and one weak
batting season; their opportunity errors contradict a blanket foreign boost.

### Ohtani: biggest value deterioration, absent comparable training profile

MLBAM 660271, origin 2017, added. NPB 2015–17 PA are 119/382/231, HR 5/22/8,
K 43/98/63. The 5/4/3 pool includes that high-K 2015 season. The held NPB fit
has eleven movers but no under-25/high-K/lower-HR match. The forecast is two-way
hinted, yet no role-specific batting development exists. No domestic coordinate
range warning does NOT mean this young two-way profile is supported.

New HR probability is 3.92% versus 22/367 = 5.99% actual; K 27.23% versus
27.79% actual. HR contributes +0.566 wins/600, singles +0.826 and walks +0.513,
partly offset by doubles/triples. Rate improves on the old 0.652 but deteriorates
from the added anchor's 1.927 to 0.840. Fixed 7.19% participation and 171.68
conditional PA yield 12.34 expected PA; value falls 0.0776 to 0.0552 versus
3.388 actual. Do not call the old domestic anchor well-founded merely because
it happened to be closer. Peers Thames, Adduci and Romero are mostly older
returners, including a non-arrival—not substitutes for young NPB support.

### Suzuki: biggest value gain is not the best hitting estimate

MLBAM 673548, origin 2021, added. NPB 2019–21 give 612/514/533 PA, 28/25/38 HR
and 81/73/88 K. The translated source pools 6,557 recency-weighted PA units;
these are not independent observations. Held domestic HR slope is 0.682, NPB
HR offset -0.168. The resulting K/HR probabilities are 17.19%/4.06%, versus
24.66%/3.14% observed in 446 MLB PA. Value terms: walks +1.131, singles +0.744,
HR +0.813, doubles/triples -0.495 together; sum +2.211 wins/600.

This is much more plausible than the added anchor's -2.337, but the old +1.794
translation is closer to actual +1.175. Thirteen held NPB movers contain no
same age/contact/power intersection. Fixed 24.62% participation times 102.88
conditional PA gives 25.33 PA and 0.173 value, versus 446 PA and 2.271 actual.
Nearest peers Roberto Ramos and Aderlin Rodriguez do not arrive; Ha-Seong Kim
has newer MLB evidence and keeps the current route. Better source representation
is useful here, but neither talent nor opportunity is nailed down.

### Yoshida: excessive talent compensates for insufficient PA

MLBAM 807799, origin 2022, added. NPB 2020–22: 492/455/508 PA, just 29/26/41 K,
14/21/21 HR. Low source K and high singles carry the prediction. Singles add
1.464 wins/600, UBB +0.697, HR +0.486. New K/HR are 9.47%/3.32%; actual are
13.97%/2.59% in 580 PA. Thirteen NPB movers include no same-profile intersection.

Rate rises 0.229 to 2.874 although actual is 1.093. Fixed 32.83% participation
times 108.09 conditional PA gives 35.49 PA. Contribution rises 0.125 to 0.281
and therefore gets closer to 2.872 actual. This is a WORSE talent prediction
and a better product error, not a successful talent repair. Peers Suzuki
(already MLB), Machado (no return) and Tucker (no return) make the heterogeneous
employment problem visible. The later Yoshida control below stays unchanged.

### Lee: nearly correct product, wrong components

MLBAM 808982, origin 2023, added. KBO 2021–23: 544/627/387 PA, 37/32/23 K,
7/23/6 HR. Seven held KBO movers include no same-profile intersection. Direct
rate +1.502 has UBB +0.755, doubles +0.458 and triples +0.550, offset by HR
-0.722. Predicted triples and power depend on tiny selected mover calibration;
there is no park adjustment to certify them.

Fixed 30.57% participation times 104.18 conditional PA gives 31.84 PA versus
158 actual. Actual hitting is -1.144, not +1.502; actual HR 2/158 versus 2.51%
predicted. Contribution 0.178 versus 0.188 actual looks excellent only because
low PA and high talent cancel. It cannot validate the hitting estimate. Peers
Yoshida/Suzuki have newer MLB work; Brosseau does not arrive. Later injury is
not used to tune the forecast or explain away the source-only talent miss.

### Hyeseong Kim: the count repair makes talent worse

MLBAM 808975, origin 2024, original saved display name is missing; the human
label is not a new forecast-time input. KBO 2022–24: 566/621/567 PA, 83/77/62 K,
4/7/11 HR. Nine held movers include one same-profile match. New K is 19.02%
against 30.59% actual; HR 1.18% against 1.76% actual. Singles add +1.210, HR
subtracts 1.853 wins/600. Rate worsens from -1.033 to -1.223, versus -0.342
actual; old translation -0.742 was better than either.

Positive dated job context is collected, but the unchanged current head still
assigns 0.47% participation and 76.42 conditional PA: 0.36 expected PA versus
170 actual. Those source fields are not a new head in this test. Peers Perlaza
(no arrival), Lee (617 actual PA) and Yoshida (205) show why MLB identity alone
cannot establish either employment or future workload. This is the only
original fresh newcomer with observed MLB PA; its bootstrap interval is a
one-person degeneracy, not population evidence.

### Henry Ramos: baseline talent was already better

MLBAM 592656, origin 2022. Only 80 KBO PA, 18 K, four UBB and three HR supersede
2021 MLB's 55 PA. Six held KBO movers, one matching intersection. New translated
rate -0.625 is much better than old -0.202, but current -0.703 is closer to
actual -0.688 over 86 PA. HBP +0.631 and triples +0.616 value terms counter
walk/double penalties—especially suspect personal signals from eighty PA.
Fixed 7.44% participation and 82.16 conditional PA give 6.11 PA. It is workload,
not deficient baseline talent, that chiefly misses delivered value. Peers
Dixon, Freitas and McCarthy include one MLB return and two non-arrivals.

### Adduci: ordinary active case, no decisive calibration win

MLBAM 451192, origin 2016. KBO 2015–16 provide 594/272 PA, 28/7 HR and 118/59 K,
after MLB 2013–14's 148 combined PA. Three held KBO movers, no matching profile.
Walk/HR terms -0.612/-0.774 partly offset doubles/triples; new -0.541 is closer
than baseline -1.078 to -0.264 observed, but old -0.204 was closest. The
unchanged 5.17% times 64.07 PA is 3.32 PA versus 93 actual. The Park/Pill/Kim
peer set is the same failed/successful mixed set as Thames, not three certified
MLB-return predictions.

### Dixon and Machado: tiny targets cannot establish precise talent

Dixon, MLBAM 641525, origin 2021: 123 NPB PA, 42 K, four HR, after 544 MLB PA
in 2018–19 and fourteen in 2020. Eight held NPB movers, no matching high-K
profile. The -2.032 singles value term pulls new rate to -1.174, little changed
from -1.147. Actual -4.542 comes from only fourteen PA; new value 0.0124 versus
-0.0621 actual is marginally closer. Palka/Freitas do not return; Bethancourt
gets 333 PA on a different current route. The count fit excludes domestic
2020 pairs; recording Dixon's source history does not erase the COVID boundary.

Machado, MLBAM 553988, origin 2021, added: KBO 2020–21 560/539 PA, 12/5 HR,
60/65 K; earlier MLB includes 233 PA in 2018. Six held KBO movers, no matching
intersection at the forecast-information age. HR subtracts 1.541 wins/600,
singles -0.759. New -2.340 is closer to observed -3.310 than anchor -0.232,
but target is just seventeen PA. Fixed 1.67% times 82.20 PA gives 1.37 PA and
-0.0011 value versus -0.0405 actual. Tsutsugo and Ha-Seong Kim are actual
participants on newer domestic routes; Romero does not arrive. No general
precision claim follows from these two tiny observed batting samples.

### Hwang: directionally useful, still weak evidence

MLBAM 666561, origin 2016, added. KBO 2014–16: 550/596/559 PA, 12/26/27 HR,
86/122/66 K. Three held KBO movers, one age/contact/power match. HR -0.674
offsets singles/doubles/triples in the -0.351 translation. It lowers the added
anchor's implausibly optimistic +1.763 toward the -5.451 observed, but that
observation is only 57 PA with one HR. Fixed 0.71% times 71.43 yields 0.51 PA;
contribution 0.0013 versus -0.342 actual. Thames, Hyun Soo Kim and Park include
a successful return, a weak active season and a non-arrival. The small target
and three-mover fit prohibit a broad claim about Korean hitters.

## Non-arrivals and unchanged controls

**Schwindel, MLBAM 643524, origin 2023:** seventy NPB PA, seventeen K, zero UBB,
one HR replace his 566 prior MLB PA (259 in 2021, 292 in 2022, fifteen in 2019).
The zero-walk source is outside the held domestic walk-coordinate range. New
walk probability 1.51% generates -2.383 wins/600 by itself, HR -1.140; total
-4.802 versus current -0.691. Fixed 14.38% times 184.77 PA gives 26.57 expected
PA and -0.130 value, versus zero delivered because he does not return. This
is the largest original value harm, not proof that his unobserved talent is
zero. Dropping substantial MLB history for a seventy-PA foreign sample is a
real design weakness, even though the route and calculation followed contract.
Peers Ramos, Aquino and Gerber also do not arrive; their losses stay counted.

**Soto, MLBAM 519304, origin 2018:** 41 HR in 459 NPB PA follows very little MLB
work and later domestic minor work. New +1.323 is driven by HR +2.578 wins/600;
the source HR coordinate exceeds domestic training range. Ten held NPB movers
contain no same-profile match. Fixed 6.17% times 130.93 PA gives 8.08 expected
PA and +0.0427 value versus zero actual; old translated +0.548 generated less
false delivered value. Neither result establishes his unobserved MLB talent.
Almonte, Hoying and Hyun Soo Kim are the outcome-blind peers; all remain overseas
or otherwise do not appear in MLB the target year. A country/identity flag is
not an MLB employment record.

**Gomez, MLBAM 450855, origin 2016:** the ordinary non-arrival selected by stable
ID. NPB 2014–16 have 616/601/554 PA and 26/17/22 HR. Six held NPB movers, two
matching profiles. Walk +0.632 offsets doubles/triples and produces almost
neutral +0.045 talent. Fixed 0.28% times 62.88 PA gives 0.17 PA and only 0.00055
false delivered value. There is no evidence for predicting his talent as zero.
Dae-Ho Lee, Murton and Tanaka also have zero target MLB PA. This ordinary small
error cannot erase the larger Schwindel/Soto errors.

**Yoshida origin 2024:** his 580+421 newer MLB PA block the old 2022 NPB route.
Current +0.327 talent and 476.22 expected PA remain unchanged versus -0.444 and
205 actual in 2025. The stale overseas-only diagnostic is not substituted.
Goodrum/Brosseau (non-arrivals) and Young (47 PA) remain the peers. This control
proves route integrity, not improved workload or hitting accuracy.

**Lee origin 2024:** 158 newer MLB PA block the old KBO route. Current -0.646
and 153.65 PA remain unchanged versus +0.463 and 617 actual in 2025. Yoshida,
Montes and Young are the peers, including tiny ten-PA Montes. Avoiding a stale
replacement is sensible, but this binary route does not answer how much
earlier KBO evidence should help after a brief MLB season.

**Thames origin 2017:** 551 newer MLB PA block KBO. +0.370 and 444.35 PA stay
unchanged versus +0.622 and 278 actual. Adduci/Hwang/Jimenez include an active
return and two non-arrivals. The prior translated talent is a diagnostic only.

**Ohtani origin 2018:** 367 newer MLB PA block NPB. +1.576 and 391.04 PA stay
unchanged versus +1.674 and 425 actual. This is the ordinary well-predicted
control, not a win for count calibration. Thames/Adduci/Choice retain their
actual successful, tiny-sample and zero-return outcomes.

## What the walks change about the decision

Count loss repairs a legitimate mathematical specification concern; it is not
a validated cure. Both opportunity and talent must be reviewed separately.
Yoshida/Lee show error cancellation; Thames/Suzuki show useful foreign production
but far too little unchanged workload; Ohtani/Hyeseong show worse talent;
Schwindel shows too much trust in a tiny latest foreign sample. Eight of eleven
active cases have zero matching mover intersections; several others have one.
Support counts are descriptive age/contact/power bins at the dated information
age, not proof of identical baseball development or market situations.

Equal-origin rate scoring gives a fourteen-PA Dixon target one quarter of the
original active-origin weight. Under the exploratory pooled-PA diagnostic, old
translation beats count calibration for both original fresh participants
(0.541 versus 0.574 RMSE) and additions (2.133 versus 2.207). These diagnostics
do not replace the locked primary score. They qualify any claim that the new
likelihood is better. Non-arrival value errors worsen, even though signed total
value moves toward zero by cancellation. Keep the current model and retain
the new method as research only. The next step is an inventory of existing
dated overseas opportunity evidence/candidates, not another weight tweak or
repetition of this calibration experiment.
